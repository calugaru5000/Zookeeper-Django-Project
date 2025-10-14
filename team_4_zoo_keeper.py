"""
Team 4 — Zoo Keeper (Django mini project)
"""

# =============================
# 0) COMMON BOOT-UP RECIPE
# =============================
# 1) Create project & app
#    python -m venv .venv && source .venv/bin/activate
#    pip install "django==5.0.*"
#    django-admin startproject proj
#    cd proj
#    python manage.py startapp app
#
# 2) Wire app & auth
#    settings.py: add 'app' to INSTALLED_APPS
#    urls.py (project):
#       from django.contrib import admin
#       from django.urls import path, include
#       urlpatterns = [
#         path('admin/', admin.site.urls),
#         path('accounts/', include('django.contrib.auth.urls')),
#         path('', include('app.urls')),
#       ]
#    settings.py: LOGIN_URL='/accounts/login/', LOGIN_REDIRECT_URL='/', LOGOUT_REDIRECT_URL='/'
#    templates/registration/login.html: basic login form (Django will render defaults if omitted)
#
# 3) DB & superuser
#    python manage.py makemigrations
#    python manage.py migrate
#    python manage.py createsuperuser
#
# 4) Run
#    python manage.py runserver

# =============================
# PROJECT SUMMARY
# =============================
# Keep a roster of animals. Filter by species/enclosure. POST action to mark an animal as fed now.

# =============================
# DATA MODEL (suggested)
# =============================
# TODO[A] MODELS
# class Species(models.Model):
#     DIETS  ex: ("herbivore","Herbivore")
#     name
#     diet
#     def __str__(self): return f"{self.name} ({self.get_diet_display()})"
#
# class Animal(models.Model):
#     owner
#     name
#     species
#     enclosure
#     last_fed_at
#     created_at
#     def __str__(self): return self.name
# admin.py: register with filters (species, enclosure, created_at) and search (name)

# =============================
# REQUIRED PAGES / URLS
# =============================
# '/'                    → Animal list (filters: species, enclosure; search: name)
# '/animals/create/'     → Create animal
# '/animals/<id>/'       → Detail with "Mark as fed" button (POST)
# '/animals/<id>/update/' '/animals/<id>/delete/'
# '/animals/<id>/feed/'  → POST action to set last_fed_at=timezone.now()

# =============================
# STEP-BY-STEP CHECKLIST
# =============================
# TODO[A] MODELS & ADMIN
# - Implement Species & Animal; migrate; admin registration
#
# TODO[B] VIEWS & URLCONF
# - ListView owner-scoped; filter by ?species=&?enclosure=&?q=
# - DetailView owner-scoped
# - feed_view(LoginRequired, POST only): update Animal.last_fed_at then redirect back
# - CRUD CBVs for create/update/delete; set owner in form_valid
#
# TODO[C] TEMPLATES & UX
# - base.html nav: Animals | Add | Login/Logout
# - animal_list.html: filters + search + badges for "Needs feeding" (if last_fed_at is None or >24h)
# - animal_detail.html: show fields + POST form button to feed
# - forms and confirm_delete

# =============================
# ACCEPTANCE CRITERIA
# =============================
# - Owner scoping everywhere
# - "Mark as fed" updates timestamp and survives refresh
# - Filters/search operate on current user’s animals

# =============================
# STRETCH
# =============================
# - Highlight animals not fed in last 24h
# - Species list page with quick add
