from decimal import Decimal, InvalidOperation

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect

from .models import Company, UserProfile, RequestForQuotation, Offer
from django.views.decorators.http import require_http_methods
from django.shortcuts import render
from django.middleware.csrf import get_token

def get_user_profile(user):
    return get_object_or_404(UserProfile, user=user)


def page(title, content):
    html = f"""
    <!DOCTYPE html>
    <html lang="ro">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{title}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                max-width: 1000px;
                margin: 40px auto;
                padding: 20px;
                background: #f4f6f9;
                color: #202b3c;
            }}
            h1 {{ color: #123b67; }}
            .card {{
                background: white;
                padding: 20px;
                margin: 15px 0;
                border-radius: 10px;
                box-shadow: 0 2px 8px #0001;
            }}
            input, textarea, button {{
                padding: 10px;
                margin: 6px 0;
                max-width: 100%;
            }}
            button {{
                background: #123b67;
                color: white;
                border: 0;
                border-radius: 5px;
                cursor: pointer;
            }}
            a {{ color: #1459a6; }}
        </style>
    </head>
    <body>
        {content}
    </body>
    </html>
    """
    return HttpResponse(html)


@login_required
def dashboard(request):
    profile = get_user_profile(request.user)
    company = profile.company

    content = f"""
        <h1>Platformă de Sourcing</h1>
        <div class="card">
            <h2>{company.name}</h2>
            <p>Rol: {profile.get_role_display()}</p>
            <p>Bun venit, {request.user.username}!</p>
            <p><a href="/sourcing/requests/">Vezi cererile de ofertă</a></p>
            <p><a href="/admin/">Administrare</a></p>
        </div>
    """
    return page("Platformă de Sourcing", content)


@login_required
def request_list(request):
    profile = get_user_profile(request.user)
    company = profile.company

    if profile.role == Company.CLIENT:
        requests_list = RequestForQuotation.objects.filter(
            client=company
        ).order_by("-created_at")
    elif profile.role == Company.SUPPLIER:
        requests_list = RequestForQuotation.objects.filter(
            invited_suppliers=company,
            is_open=True
        ).order_by("-created_at")
    else:
        return HttpResponse("Rol nepermis.", status=403)

    content = "<h1>Cereri de ofertă</h1><p><a href='/sourcing/'>Înapoi</a></p>"

    for rfq in requests_list:
        content += f"""
            <div class="card">
                <h2>{rfq.title}</h2>
                <p>Termen limită: {rfq.deadline}</p>
                <p>Status: {"Deschisă" if rfq.is_open else "Închisă"}</p>
                <p><a href="/sourcing/requests/{rfq.pk}/">Vezi detalii</a></p>
            </div>
        """

    if not requests_list:
        content += "<p>Nu există cereri disponibile.</p>"

    return page("Cereri de ofertă", content)


@login_required
def request_detail(request, request_id):
    profile = get_user_profile(request.user)
    company = profile.company

    if profile.role == Company.CLIENT:
        rfq = get_object_or_404(
            RequestForQuotation,
            pk=request_id,
            client=company
        )
    elif profile.role == Company.SUPPLIER:
        rfq = get_object_or_404(
            RequestForQuotation,
            pk=request_id,
            invited_suppliers=company
        )
    else:
        return HttpResponse("Rol nepermis.", status=403)

    offers = Offer.objects.filter(request=rfq).select_related("supplier")

    content = f"""
        <h1>{rfq.title}</h1>
        <div class="card">
            <p>Termen limită: {rfq.deadline}</p>
            <p>Status: {"Deschisă" if rfq.is_open else "Închisă"}</p>
        </div>
        <p><a href="/sourcing/requests/">Înapoi la cereri</a></p>
    """

    if profile.role == Company.SUPPLIER:
        existing_offer = offers.filter(supplier=company).first()

        if rfq.is_open:
            content += f"""
                <div class="card">
                    <h2>{"Actualizează oferta" if existing_offer else "Trimite oferta"}</h2>
                    <form method="post" action="/sourcing/requests/{rfq.pk}/offer/">
                        <input type="hidden" name="csrfmiddlewaretoken"
                               value="{request.META.get('CSRF_COOKIE', '')}">
                        <label>Preț unitar (EUR):</label><br>
                        <input type="number" name="price" step="0.01" min="0"
                               value="{existing_offer.price if existing_offer else ''}" required><br>
                        <label>Zile pentru livrare:</label><br>
                        <input type="number" name="delivery_days" min="0"
                               value="{existing_offer.delivery_days if existing_offer else 0}" required><br>
                        <label>Comentarii:</label><br>
                        <textarea name="comments">{existing_offer.comments if existing_offer else ''}</textarea><br>
                        <button type="submit">Trimite oferta</button>
                    </form>
                </div>
            """
        else:
            content += "<p>Această cerere este închisă.</p>"

    if profile.role == Company.CLIENT:
        content += "<h2>Oferte primite</h2>"

        if not offers.exists():
            content += "<p>Nu au fost trimise încă oferte.</p>"

        for offer in offers:
            content += f"""
                <div class="card">
                    <h3>{offer.supplier.name}</h3>
                    <p>Preț unitar: {offer.price} {offer.currency}</p>
                    <p>Livrare: {offer.delivery_days} zile</p>
                    <p>Comentarii: {offer.comments or "—"}</p>
                    <p>Status: {"Selectată" if offer.is_selected else "În evaluare"}</p>
                </div>
            """

    return page("Detalii cerere", content)


@login_required
def submit_offer(request, request_id):
    if request.method != "POST":
        return HttpResponse("Metodă nepermisă.", status=405)

    profile = get_user_profile(request.user)

    if profile.role != Company.SUPPLIER:
        return HttpResponse("Doar furnizorii pot trimite oferte.", status=403)

    rfq = get_object_or_404(
        RequestForQuotation,
        pk=request_id,
        invited_suppliers=profile.company,
        is_open=True
    )

    try:
        price = Decimal(request.POST.get("price", ""))
        delivery_days = int(request.POST.get("delivery_days", "0"))

        if not price.is_finite() or price < 0 or delivery_days < 0:
            raise ValueError
    except (InvalidOperation, ValueError):
        return HttpResponse("Prețul sau termenul de livrare nu este valid.", status=400)

    Offer.objects.update_or_create(
        request=rfq,
        supplier=profile.company,
        defaults={
            "price": price,
            "currency": "EUR",
            "delivery_days": delivery_days,
            "comments": request.POST.get("comments", ""),
            "submitted_at": __import__("django.utils.timezone", fromlist=["now"]).now(),
        }
    )

    return redirect(f"/sourcing/requests/{rfq.pk}/")

def home(request):
    if request.user.is_authenticated:
        try:
            profile = request.user.sourcing_profile
            if profile.role == "CLIENT":
                return redirect("client_dashboard")
            return redirect("supplier_dashboard")
        except UserProfile.DoesNotExist:
            pass

    return page(
        "Airbus Sourcing Platform",
        """
        <style>
            body {
                margin: 0;
                padding: 0;
                max-width: none;
                font-family: Arial, Helvetica, sans-serif;
                color: #ffffff;
                background: #061a35;
            }

            .home-hero {
                min-height: 650px;
                padding: 55px 6%;
                box-sizing: border-box;
                position: relative;
                overflow: hidden;
                background:
                    linear-gradient(90deg,
                        rgba(3, 20, 48, 0.92) 0%,
                        rgba(3, 20, 48, 0.68) 48%,
                        rgba(3, 20, 48, 0.12) 100%),
                    url("https://images.unsplash.com/photo-1436491865332-7a61a109cc05?auto=format&fit=crop&w=2000&q=85")
                    center/cover no-repeat;
            }

            .welcome {
                margin-top: 35px;
                font-size: 13px;
                letter-spacing: 5px;
                text-transform: uppercase;
                color: #c5d9f5;
            }

            .hero-title {
                max-width: 780px;
                font-size: clamp(42px, 6vw, 76px);
                line-height: 1.08;
                margin: 18px 0;
                color: white;
            }

            .hero-description {
                max-width: 620px;
                font-size: 20px;
                line-height: 1.6;
                color: #edf4ff;
            }

            .benefits {
                display: flex;
                flex-wrap: wrap;
                gap: 28px;
                margin: 35px 0;
                color: white;
            }

            .benefit {
                border-left: 2px solid #8db9f4;
                padding-left: 12px;
                font-size: 15px;
            }

            .interface-cards {
                display: flex;
                flex-wrap: wrap;
                gap: 18px;
                margin-top: 35px;
            }

            .interface-card {
                box-sizing: border-box;
                width: 330px;
                max-width: 100%;
                padding: 24px;
                border-radius: 14px;
                text-decoration: none;
                transition: transform 0.2s, background 0.2s;
            }

            .interface-card:hover {
                transform: translateY(-5px);
            }

            .client-card {
                background: #082b60;
                color: white;
                border: 1px solid #7da9e6;
            }

            .supplier-card {
                background: rgba(255, 255, 255, 0.94);
                color: #092650;
            }

            .interface-card h2 {
                margin: 0 0 12px;
                font-size: 22px;
                color: inherit;
            }

            .interface-card p {
                line-height: 1.6;
                margin-bottom: 18px;
            }

            .card-link {
                display: inline-block;
                font-weight: bold;
                color: inherit;
            }

            .features {
                display: grid;
                grid-template-columns: repeat(4, minmax(0, 1fr));
                gap: 1px;
                background: rgba(255,255,255,0.2);
                margin-top: 45px;
                border: 1px solid rgba(255,255,255,0.25);
                border-radius: 14px;
                overflow: hidden;
            }

            .feature {
                padding: 22px;
                background: rgba(5, 25, 55, 0.83);
            }

            .feature h3 {
                font-size: 16px;
                margin-top: 0;
            }

            .feature p {
                font-size: 14px;
                line-height: 1.5;
                color: #e0eaf8;
                margin-bottom: 0;
            }

            @media (max-width: 800px) {
                .home-hero {
                    padding: 35px 5%;
                }

                .features {
                    grid-template-columns: repeat(2, minmax(0, 1fr));
                }

                .hero-description {
                    font-size: 17px;
                }
            }

            @media (max-width: 480px) {
                .features {
                    grid-template-columns: 1fr;
                }
            }
        </style>

        <section class="home-hero">
            <div class="welcome">Handcrafted by Horia</div>

            <h1 class="hero-title">Sourcing Platform</h1>

            <p class="hero-description">
                Connecting the company with trusted suppliers for a more 
                innovative and sustainable future.
            </p>

            <div class="benefits">
                <div class="benefit">Transparent<br>Procurement</div>
                <div class="benefit">Efficient<br>Collaboration</div>
                <div class="benefit">Sustainable<br>Supply Chain</div>
            </div>

            <div class="interface-cards">
                <a class="interface-card client-card" href="/client/">
                    <h2>▣ Client Interface</h2>
                    <p>
                        Create and manage sourcing requests, compare offers
                        and select suppliers.
                    </p>
                    <span class="card-link">Explore client area →</span>
                </a>

                <a class="interface-card supplier-card" href="/supplier/">
                    <h2>♟ Supplier Interface</h2>
                    <p>
                        View sourcing requests, submit your quotations
                        and collaborate with Airbus.
                    </p>
                    <span class="card-link">Explore supplier area →</span>
                </a>
            </div>

            <div class="features">
                <div class="feature">
                    <h3>▤ Sourcing Requests</h3>
                    <p>
                        Publish detailed requirements for products
                        and services.
                    </p>
                </div>

                <div class="feature">
                    <h3>♟ Supplier Quotations</h3>
                    <p>
                        Receive and compare offers from approved suppliers.
                    </p>
                </div>

                <div class="feature">
                    <h3>▥ Evaluation &amp; Selection</h3>
                    <p>
                        Analyze proposals and choose the best supplier.
                    </p>
                </div>

                <div class="feature">
                    <h3>✓ Secure &amp; Compliant</h3>
                    <p>
                        A transparent procurement process with controlled
                        access to sourcing information.
                    </p>
                </div>
            </div>
        </section>
        """
    )

@require_http_methods(["GET", "POST"])
def client_interface(request):
    if request.method == "POST":
        company_name = request.POST.get("company_name", "").strip()
        country = request.POST.get("country", "").strip()
        city = request.POST.get("city", "").strip()
        category = request.POST.get("category", "").strip()
        delivery_address = request.POST.get("delivery_address", "").strip()
        contact_name = request.POST.get("contact_name", "").strip()
        email = request.POST.get("email", "").strip()
        requirements = request.POST.get("requirements", "").strip()

        if not all([
            company_name, country, city, category,
            delivery_address, contact_name, email
        ]):
            return render(request, "sourcing/client_interface.html", {
                "error": "Completează toate câmpurile obligatorii."
            })

        # În pasul următor vom salva datele în baza de date.
        return render(request, "sourcing/client_interface.html", {
            "success": "Datele au fost completate. Urmează configurarea salvării în baza de date."
        })

    return render(request, "sourcing/client_interface.html")
def supplier_interface(request):
    content = f"""
    <style>
        body {
                margin: 0;
    padding: 0;
    font-family: Arial, Helvetica, sans-serif;
    color: #202b3c;

    background:
        linear-gradient(
            rgba(5, 20, 45, 0.72),
            rgba(5, 20, 45, 0.82)
        ),
        url("https://images.unsplash.com/photo-1497366754035-f200968a6e72?auto=format&fit=crop&w=1920&q=85");

    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
    background-attachment: fixed;
    min-height: 100vh;
        }

        .supplier-container {
            max-width: 1000px;
            margin: 40px auto;
            padding: 20px;
        }

        .supplier-container h1 {
            color: white;
            font-size: 38px;
            margin-bottom: 12px;
        }

        .supplier-description {
            color: #e5edf8;
            margin-bottom: 28px;
            line-height: 1.6;
        }

        .supplier-card {
            background: #ffffff;
            padding: 30px;
            border-radius: 18px;
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.15);
        }

        .supplier-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 18px 22px;
        }

        .supplier-field {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .supplier-field.full {
            grid-column: 1 / -1;
        }

        .supplier-field label {
            font-weight: 600;
            font-size: 14px;
        }

        .supplier-field input,
        .supplier-field select,
        .supplier-field textarea {
            box-sizing: border-box;
            width: 100%;
            padding: 13px;
            border: 1px solid #cbd5e1;
            border-radius: 9px;
            background: #fff;
            color: #202b3c;
            font: inherit;
        }

        .supplier-field textarea {
            resize: vertical;
            min-height: 100px;
        }

        .supplier-field input:focus,
        .supplier-field select:focus,
        .supplier-field textarea:focus {
            outline: 2px solid #93c5fd;
            border-color: #2563eb;
        }

        .supplier-submit {
            margin-top: 22px;
            padding: 14px 24px;
            border: 0;
            border-radius: 8px;
            background: #123b76;
            color: white;
            font-weight: bold;
            cursor: pointer;
        }

        .supplier-submit:hover {
            background: #1d4f91;
        }

        @media (max-width: 650px) {
            .supplier-grid {
                grid-template-columns: 1fr;
            }

            .supplier-field.full {
                grid-column: auto;
            }

            .supplier-card {
                padding: 20px;
            }
        }
    </style>

    <div class="supplier-container">
        <h1>Supplier Interface</h1>
        <p class="supplier-description">
            Register your company and describe the IT products and
            services you offer to potential business customers.
        </p>

        <div class="supplier-card">
            <h2>Company Information</h2>
            <p>Fields marked with * are mandatory.</p>

              <input type="hidden" name="csrfmiddlewaretoken" value="{get_token(request)}">

                <div class="supplier-grid">
                    <div class="supplier-field">
                        <label>Company name *</label>
                        <input type="text" name="company_name"
                               placeholder="Company name" required>
                    </div>

                    <div class="supplier-field">
                        <label>Country *</label>
                        <input type="text" name="country"
                               placeholder="e.g. Romania" required>
                    </div>

                    <div class="supplier-field">
                        <label>City *</label>
                        <input type="text" name="city"
                               placeholder="e.g. Bucharest" required>
                    </div>

                    <div class="supplier-field">
                        <label>Contact person *</label>
                        <input type="text" name="contact_name"
                               placeholder="Full name" required>
                    </div>

                    <div class="supplier-field">
                        <label>Business email *</label>
                        <input type="email" name="email"
                               placeholder="name@company.com" required>
                    </div>

                    <div class="supplier-field">
                        <label>Product or service category *</label>
                        <select name="category" required>
                            <option value="">Select a category</option>
                            <option value="IT Hardware">IT Hardware — laptops, computers, phones</option>
                            <option value="IT Services">IT Services — support, consulting</option>
                            <option value="Networking">Networking and infrastructure</option>
                            <option value="Software">Software and licences</option>
                            <option value="Other">Other</option>
                        </select>
                    </div>

                    <div class="supplier-field full">
                        <label>Products and services offered *</label>
                        <textarea name="products_services" rows="4"
                            placeholder="Describe your products and services"
                            required></textarea>
                    </div>

                    <div class="supplier-field">
                        <label>Payment terms *</label>
                        <select name="payment_terms" required>
                            <option value="">Select payment terms</option>
                            <option value="30 days">Net 30 days</option>
                            <option value="60 days">Net 60 days</option>
                            <option value="90 days">Net 90 days</option>
                            <option value="Advance payment">Advance payment</option>
                            <option value="Negotiable">Negotiable</option>
                        </select>
                    </div>

                    <div class="supplier-field">
                        <label>Delivery terms *</label>
                        <select name="delivery_terms" required>
                            <option value="">Select delivery terms</option>
                            <option value="EXW">EXW</option>
                            <option value="FCA">FCA</option>
                            <option value="DAP">DAP</option>
                            <option value="DDP">DDP</option>
                            <option value="Negotiable">Negotiable</option>
                        </select>
                    </div>

                    <div class="supplier-field full">
                        <label>Additional information</label>
                        <textarea name="additional_info" rows="3"
                            placeholder="Certifications, delivery capacity, other details"></textarea>
                    </div>
                </div>

                <button class="supplier-submit" type="submit">
                    Submit supplier profile
                </button>
            </form>
        </div>
    </div>
    """
    return page("Supplier Interface", content)
