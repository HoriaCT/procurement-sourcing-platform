from django.db import models
from django.contrib.auth.models import User


class Company(models.Model):
    CLIENT = "CLIENT"
    SUPPLIER = "SUPPLIER"

    TYPES = [
        (CLIENT, "Client"),
        (SUPPLIER, "Furnizor"),
    ]

    name = models.CharField(max_length=200)
    company_type = models.CharField(max_length=10, choices=TYPES)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    CLIENT = "CLIENT"
    SUPPLIER = "SUPPLIER"

    ROLES = [
        (CLIENT, "Client"),
        (SUPPLIER, "Furnizor"),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="sourcing_profile",
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.PROTECT,
    )
    role = models.CharField(max_length=10, choices=ROLES)

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.role != self.company.company_type:
            raise ValidationError(
                "Rolul utilizatorului trebuie să corespundă firmei."
            )

    def __str__(self):
        return f"{self.user.username} - {self.company.name}"


class RequestForQuotation(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    client = models.ForeignKey(
        Company,
        on_delete=models.PROTECT,
        related_name="requests",
        limit_choices_to={"company_type": "CLIENT"},
    )
    invited_suppliers = models.ManyToManyField(
        Company,
        related_name="invitations",
        limit_choices_to={"company_type": "SUPPLIER"},
        blank=True,
    )
    deadline = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_open = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class Offer(models.Model):
    request = models.ForeignKey(
        RequestForQuotation,
        on_delete=models.CASCADE,
        related_name="offers",
    )
    supplier = models.ForeignKey(
        Company,
        on_delete=models.PROTECT,
        related_name="offers",
    )
    price = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="EUR")
    delivery_days = models.PositiveIntegerField(default=0)
    comments = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    is_selected = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["request", "supplier"],
                name="unique_offer_per_supplier_request",
            )
        ]

    def __str__(self):
        return f"{self.supplier.name} - {self.price} {self.currency}"
