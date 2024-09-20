from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    pass


class Product(models.Model):
    name = models.CharField(max_length=50)
    image = models.ImageField(null=True, blank=True)
    price = models.IntegerField(default=0)
    explanation = models.TextField(max_length=300)
    created_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.name


class OrderHistroy(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="has_ordered")
    product = models.ForeignKey(
        Product, on_delete=models.SET_NULL, null=True, related_name="product_histroy"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    price = models.IntegerField(default=0)
    num = models.IntegerField(default=1)

    def __str__(self) -> str:
        return f"<購入者:{self.user.username} 商品名:{self.product.name}>"
