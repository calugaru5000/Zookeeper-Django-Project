# proj/zookeeper/views.py
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from .forms import AnimalForm, SpeciesForm, CustomUserCreationForm, CustomUserChangeForm, EnclosureForm

from .models import Animal, Species, Enclosure
from django.shortcuts import render


# 1️⃣ List View — show only the logged-in user's animals, with filters
class AnimalListView(LoginRequiredMixin, ListView):
    model = Animal
    template_name = 'Zoo/animals_list.html'
    context_object_name = 'animals'

    def get_queryset(self):
        # Show all animals to users; editing/feeding is restricted elsewhere
        qs = Animal.objects.all()
        species = self.request.GET.get('species')
        enclosure = self.request.GET.get('enclosure')
        q = self.request.GET.get('q')

        if species:
            qs = qs.filter(species__id=species)
        if enclosure:
            # Filter by enclosure name (enclosure is a FK)
            qs = qs.filter(enclosure__name__icontains=enclosure)
        if q:
            qs = qs.filter(name__icontains=q)

        return qs.select_related('species', 'enclosure')
    def get_context_data(self,**kwargs):
        context = super().get_context_data(**kwargs)
        context['species_list'] = Species.objects.all()
        context['enclosure_list'] = Enclosure.objects.all()
        return context

# 2️⃣ Detail View — also restricted to current user
class AnimalDetailView(LoginRequiredMixin, DetailView):
    model = Animal
    template_name = 'Zoo/animal_detail.html'
    context_object_name = 'animal'

    def get_queryset(self):
        # Allow viewing details of any animal; actions are permission-checked in templates and views
        return Animal.objects.all().select_related('species', 'enclosure', 'owner')


# 3️⃣ Create / Update / Delete Views — generic CBVs
class AnimalCreateView(LoginRequiredMixin, CreateView):
    model = Animal
    form_class=AnimalForm
    template_name = 'Zoo/animal_form.html'
    success_url = reverse_lazy('animals_list')
    extra_context = {'form_title': 'Add New Animal'}

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['enclosure_list'] = Enclosure.objects.all()
        ctx['species_list'] = Species.objects.all()
        return ctx

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class AnimalUpdateView(LoginRequiredMixin, UpdateView):
    model = Animal
    fields = ['name', 'species', 'enclosure']
    template_name = 'Zoo/animal_form.html'
    success_url = reverse_lazy('animals_list')

    def get_queryset(self):
        # Owners can edit their animals; staff can edit any
        if self.request.user.is_staff:
            return Animal.objects.all()
        return Animal.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.setdefault('form_title', 'Edit Animal')
        ctx['enclosure_list'] = Enclosure.objects.all()
        ctx['species_list'] = Species.objects.all()
        return ctx


class AnimalDeleteView(LoginRequiredMixin, DeleteView):
    model = Animal
    template_name = 'Zoo/confirm_delete.html'
    success_url = reverse_lazy('animals_list')

    def get_queryset(self):
        if self.request.user.is_staff:
            return Animal.objects.all()
        return Animal.objects.filter(owner=self.request.user)


# 4️⃣ Feed View — POST only
@require_POST
@login_required
def feed_view(request, pk):
    # Allow only the owner or staff to mark an animal as fed
    if request.user.is_staff:
        animal = get_object_or_404(Animal, pk=pk)
    else:
        animal = get_object_or_404(Animal, pk=pk, owner=request.user)
    animal.last_fed_at = timezone.now()
    animal.save()
    return redirect('animal_detail', pk=pk)


from django.contrib.auth.decorators import login_required


# 5️⃣ Simple Map View — custom rectangular map grouped by diet
@login_required
def map_view(request):
    """
    Render a custom 'map' that divides the page into three vertical zones:
    left = herbivores, middle = omnivores, right = carnivores.
    Shows only the current user's animals, grouped by species.diet.
    """
    animals = (
        Animal.objects.filter(owner=request.user)
        .select_related('species')
        .order_by('name')
    )

    herbivores = [a for a in animals if a.species and a.species.diet == 'herbivore']
    omnivores = [a for a in animals if a.species and a.species.diet == 'omnivore']
    carnivores = [a for a in animals if a.species and a.species.diet == 'carnivore']

    context = {
        'herbivores': herbivores,
        'omnivores': omnivores,
        'carnivores': carnivores,
        'counts': {
            'herbivore': len(herbivores),
            'omnivore': len(omnivores),
            'carnivore': len(carnivores),
        },
    }
    return render(request, 'Zoo/map.html', context)

# Admin Views
class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff

class AdminDashboardView(AdminRequiredMixin, TemplateView):
    template_name = 'Zoo/admin.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['animals'] = Animal.objects.all().select_related('species', 'owner', 'enclosure')
        context['species_list'] = Species.objects.all()
        context['users'] = User.objects.all()
        context['enclosures'] = Enclosure.objects.all()
        return context

# Species Management Views
class SpeciesCreateView(AdminRequiredMixin, CreateView):
    model = Species
    form_class = SpeciesForm
    template_name = 'Zoo/animal_form.html'
    success_url = reverse_lazy('admin_dashboard')
    extra_context = {'form_title': 'Add New Species'}

class SpeciesUpdateView(AdminRequiredMixin, UpdateView):
    model = Species
    form_class = SpeciesForm
    template_name = 'Zoo/animal_form.html'
    success_url = reverse_lazy('admin_dashboard')
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.setdefault('form_title', 'Edit Species')
        return ctx

class SpeciesDeleteView(AdminRequiredMixin, DeleteView):
    model = Species
    template_name = 'Zoo/confirm_delete.html'
    success_url = reverse_lazy('admin_dashboard')

# User Management Views
class UserCreateView(AdminRequiredMixin, CreateView):
    model = User
    form_class = CustomUserCreationForm
    template_name = 'Zoo/animal_form.html'
    success_url = reverse_lazy('admin_dashboard')
    extra_context = {'form_title': 'Add New User'}

class UserUpdateView(AdminRequiredMixin, UpdateView):
    model = User
    form_class = CustomUserChangeForm
    template_name = 'Zoo/animal_form.html'
    success_url = reverse_lazy('admin_dashboard')
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.setdefault('form_title', 'Edit User')
        return ctx

class UserDeleteView(AdminRequiredMixin, DeleteView):
    model = User
    template_name = 'Zoo/confirm_delete.html'
    success_url = reverse_lazy('admin_dashboard')

# Enclosure Management Views
class EnclosureCreateView(AdminRequiredMixin, CreateView):
    model = Enclosure
    form_class = EnclosureForm
    template_name = 'Zoo/animal_form.html'
    success_url = reverse_lazy('admin_dashboard')
    extra_context = {'form_title': 'Add New Enclosure'}

class EnclosureUpdateView(AdminRequiredMixin, UpdateView):
    model = Enclosure
    form_class = EnclosureForm
    template_name = 'Zoo/animal_form.html'
    success_url = reverse_lazy('admin_dashboard')
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.setdefault('form_title', 'Edit Enclosure')
        return ctx

class EnclosureDeleteView(AdminRequiredMixin, DeleteView):
    model = Enclosure
    template_name = 'Zoo/confirm_delete.html'
    success_url = reverse_lazy('admin_dashboard')
