from typing import Any

import stripe
import stripe.error
from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.db.models.query import QuerySet
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic.base import View
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView
from django.views.generic.list import ListView

from .forms import LoginForm, ProductNumForm, ProductSearchForm, SignUpForm
from .models import OrderHistroy, Product


class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = "main/signup.html"
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response


class Login(LoginView):
    authentication_form = LoginForm
    template_name = "main/login.html"


class Logout(LogoutView):
    pass


class AccountView(LoginRequiredMixin, ListView):
    template_name = "main/account.html"
    paginate_by = 5

    def get_queryset(self) -> QuerySet[Any]:
        user = self.request.user
        return user.has_ordered.order_by("-created_at")


class ProductList(ListView):
    paginate_by = "15"
    template_name = "main/home.html"

    def get_queryset(self):
        products = Product.objects.order_by("-created_at")

        form = ProductSearchForm(self.request.GET)

        if form.is_valid():
            keyword = form.cleaned_data.get("keyword")
            if keyword:
                products = products.filter(name__icontains=keyword)
        return products

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        form = ProductSearchForm(self.request.GET)
        context["form"] = form
        if form.is_valid():
            context["keyword"] = form.cleaned_data.get("keyword")
        return context


class ProductDetail(DetailView):
    model = Product

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["form"] = ProductNumForm()
        return context

    def post(self, request, *args, **kwargs):
        pk = self.kwargs["pk"]
        num = self.request.POST.get("num")

        if "cart" in self.request.session:
            # cartに入っている商品
            cart = self.request.session["cart"]
            # 入っている商品ごとの個数(辞書型)
            num_dict = self.request.session["num_dict"]

            if str(pk) in num_dict:
                num_dict[str(pk)] += int(num)
            else:
                cart.append(pk)
                num_dict[str(pk)] = int(num)
        else:
            self.request.session["cart"] = [pk]
            self.request.session["num_dict"] = {str(pk): int(num)}
        return redirect("home")


class Cart(LoginRequiredMixin, ListView):
    paginate_by = 5
    template_name = "main/cart.html"

    # get_querysetの後に実行される
    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        if "cart" in self.request.session:
            num_dict = self.request.session["num_dict"]
            context["total_price"] = sum(
                self.product_net(product, num_dict) for product in self.products
            )
            context["num_dict"] = num_dict
            context["total_num"] = sum(num_dict.values())
            context["data_key"] = settings.STRIPE_PUBLISHABLE_KEY
        else:
            context["total_price"] = 0
            context["total_num"] = 0
        return context

    def get_queryset(self):
        if "cart" in self.request.session:
            self.products = Product.objects.filter(
                pk__in=self.request.session["cart"]
            ).order_by("pk")
            return self.products
        else:
            # 空のクエリセットを返すためのメソッド
            return Product.objects.none()

    def product_net(self, product, num_dict):
        """一つの商品に対して小計を計算する関数"""
        # num_dictからproductのidを利用して数を取得
        return product.price * int(num_dict[str(product.pk)])

    def post(self, *args, **kwargs):
        pk = self.request.POST.get("delete_pk")
        cart = self.request.session["cart"]
        num_dict = self.request.session["num_dict"]
        cart.remove(int(pk))
        num_dict.pop(pk)
        self.request.session["cart"] = cart
        self.request.session["num_dict"] = num_dict
        return redirect("cart")


class CheckoutView(View):
    def post(self, *args, **kwargs):
        stripe.api_key = settings.STRIPE_API_KEY

        token = self.request.POST["stripeToken"]

        try:
            stripe.Charge.create(
                amount=int(self.request.POST["price"]),
                currency="jpy",
                source=token,
                description="BeEn_ec",
            )
        except stripe.error.CardError:
            return render(
                self.request,
                "main/error.html",
                {
                    "message": "決済に失敗しました。",
                },
            )
        purchased_products = self.request.session["cart"]
        num_dict = self.request.session["num_dict"]

        # 決済終了したいのでsessionを削除する
        del self.request.session["cart"]
        del self.request.session["num_dict"]

        for product_pk in purchased_products:
            product = Product.objects.get(pk=product_pk)
            OrderHistroy.objects.create(
                user=self.request.user,
                product=product,
                price=product.price,
                num=num_dict[str(product_pk)],
            )
        return render(
            self.request,
            "main/complete.html",
            {
                "products": Product.objects.filter(pk__in=purchased_products).order_by(
                    "pk"
                ),
                "num_dict": num_dict,
            },
        )
