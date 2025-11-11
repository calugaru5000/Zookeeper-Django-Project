# proj/zookeeper/views.py
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from .forms import AnimalForm, SpeciesForm, CustomUserCreationForm, CustomUserChangeForm, EnclosureForm
from django.http import JsonResponse

from .models import Animal, Species, Enclosure, StaffRole
from django.shortcuts import render
from datetime import timedelta
from django.db.models import Q


def can_edit_animal(user, animal):
    """Check if user can edit an animal based on enclosure-based staff role or ownership."""
    if user.is_staff:
        return True
    if animal.owner == user:
        return True
    # Check if user has keeper or manager role in the animal's enclosure
    try:
        staff_role = StaffRole.objects.get(user=user, enclosure=animal.enclosure)
        return staff_role.can_edit_animals()
    except StaffRole.DoesNotExist:
        return False

def can_feed_animal(user, animal):
    """Check if user can feed an animal."""
    if user.is_staff:
        return True
    if animal.owner == user:
        return True
    try:
        staff_role = StaffRole.objects.get(user=user, enclosure=animal.enclosure)
        return staff_role.can_edit_animals()
    except StaffRole.DoesNotExist:
        return False

def get_user_enclosures(user):
    """Get all enclosures the user is assigned to as staff."""
    if user.is_staff:
        return Enclosure.objects.all()
    return Enclosure.objects.filter(staff_assignments__user=user).distinct()

def get_user_staff_roles(user):
    """Get all staff role assignments for a user."""
    return StaffRole.objects.filter(user=user)


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
    
    # Check role-based access
    if not can_feed_animal(request.user, animal):
        return redirect('animal_detail', pk=pk)
    
    animal.last_fed_at = timezone.now()
    animal.save()

    # If AJAX request, return JSON instead of redirect
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
        return JsonResponse({
            'status': 'ok',
            'id': animal.id,
            'last_fed_at': animal.last_fed_at.isoformat()
        })

    return redirect('animal_detail', pk=pk)


from django.contrib.auth.decorators import login_required


# 5️⃣ Simple Map View — custom rectangular map grouped by diet
@login_required
def map_view(request):
    animals = Animal.objects.select_related('species', 'enclosure').order_by('name')

    herbivores = [a for a in animals if a.species and a.species.diet == 'herbivore']
    omnivores = [a for a in animals if a.species and a.species.diet == 'omnivore']
    carnivores = [a for a in animals if a.species and a.species.diet == 'carnivore']

    # 🧩 Serialize animal data
    def serialize_animal(animal):
        return {
            'id': animal.id,
            'name': animal.name,
            'species': animal.species.name if animal.species else 'Unknown',
            'enclosure': animal.enclosure.name if animal.enclosure else 'Unknown',
            'feed_url': reverse('animal_feed', args=[animal.id]),
            'can_feed': request.user.is_staff or (animal.owner_id == request.user.id),
            'last_fed_at': animal.last_fed_at.isoformat() if animal.last_fed_at else None,
        }

    # 🧹 Serialize enclosure data
    def serialize_enclosure(enc):
        return {
            'id': enc.id,
            'name': enc.name,
            'diet_type': enc.diet_type,
            'last_cleaned_at': enc.last_cleaned_at.isoformat() if getattr(enc, 'last_cleaned_at', None) else None,
        }

    context = {
        'herbivores': [serialize_animal(a) for a in herbivores],
        'omnivores': [serialize_animal(a) for a in omnivores],
        'carnivores': [serialize_animal(a) for a in carnivores],
        'enclosures': [serialize_enclosure(e) for e in Enclosure.objects.all()],
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
        context['staff_roles'] = StaffRole.objects.all().select_related('user', 'enclosure', 'assigned_by')
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

# Staff Role Management Views
class StaffRoleCreateView(AdminRequiredMixin, CreateView):
    model = StaffRole
    fields = ['user', 'enclosure', 'role']
    template_name = 'Zoo/animal_form.html'
    success_url = reverse_lazy('admin_dashboard')
    extra_context = {'form_title': 'Assign Staff Role'}

    def form_valid(self, form):
        form.instance.assigned_by = self.request.user
        return super().form_valid(form)

class StaffRoleUpdateView(AdminRequiredMixin, UpdateView):
    model = StaffRole
    fields = ['user', 'enclosure', 'role']
    template_name = 'Zoo/animal_form.html'
    success_url = reverse_lazy('admin_dashboard')
    
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.setdefault('form_title', 'Edit Staff Role')
        return ctx

class StaffRoleDeleteView(AdminRequiredMixin, DeleteView):
    model = StaffRole
    template_name = 'Zoo/confirm_delete.html'
    success_url = reverse_lazy('admin_dashboard')

@require_POST
@login_required
def clean_enclosure(request, enclosure_id):
    enclosure = get_object_or_404(Enclosure, id=enclosure_id)

    # Permission: staff or assigned role that can clean
    if not request.user.is_staff:
        role = StaffRole.objects.filter(user=request.user, enclosure=enclosure).first()
        if not role or not role.can_clean_enclosure():
            # For AJAX, return JSON error; otherwise redirect to tasks
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
                return JsonResponse({'success': False, 'error': 'permission_denied'}, status=403)
            return redirect('my_tasks')

    enclosure.last_cleaned_at = timezone.now()
    enclosure.save()

    # If AJAX request, return JSON
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
        return JsonResponse({
            'success': True,
            'last_cleaned_at': enclosure.last_cleaned_at.isoformat()
        })

    # Otherwise, redirect to My Tasks page
    return redirect('my_tasks')


class MyTasksView(LoginRequiredMixin, TemplateView):
    """Shows tasks (feeding, cleaning) for enclosures the user is assigned to via StaffRole."""
    template_name = 'Zoo/my_tasks.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user

        # Get enclosures the user is explicitly assigned to via StaffRole
        # (Do NOT fall back to all enclosures for staff here — user requested
        # My Tasks to only show assigned enclosures.)
        enclosures = Enclosure.objects.filter(staff_assignments__user=user).distinct()

        # Feeding tasks: animals in assigned enclosures not fed in last 24h
        threshold = timezone.now() - timedelta(hours=24)
        animals_qs = Animal.objects.filter(enclosure__in=enclosures).select_related('species', 'enclosure', 'owner')
        animals_needing_feed = animals_qs.filter(Q(last_fed_at__lt=threshold) | Q(last_fed_at__isnull=True))

        # Cleaning tasks: enclosures needing cleaning (older than 7 days or never cleaned)
        clean_threshold = timezone.now() - timedelta(days=7)
        enclosures_needing_clean = enclosures.filter(Q(last_cleaned_at__lt=clean_threshold) | Q(last_cleaned_at__isnull=True))

        # Build task lists with permission flags
        animal_tasks = []
        for a in animals_needing_feed:
            animal_tasks.append({
                'animal': a,
                'can_feed': can_feed_animal(user, a),
                'enclosure_role': StaffRole.objects.filter(user=user, enclosure=a.enclosure).first()
            })

        cleaning_tasks = []
        for e in enclosures_needing_clean:
            role = StaffRole.objects.filter(user=user, enclosure=e).first()
            can_clean = False
            if user.is_staff:
                can_clean = True
            elif role:
                can_clean = role.can_clean_enclosure()
            cleaning_tasks.append({
                'enclosure': e,
                'can_clean': can_clean,
                'role': role
            })

        ctx['animal_tasks'] = animal_tasks
        ctx['cleaning_tasks'] = cleaning_tasks
        ctx['user_roles'] = get_user_staff_roles(user)
        ctx['enclosures'] = enclosures
        # Outside tasks: animals and enclosures NOT in the user's assigned enclosures
        outside_enclosures = Enclosure.objects.exclude(id__in=enclosures.values_list('id', flat=True))

        outside_animals_qs = Animal.objects.filter(enclosure__in=outside_enclosures).select_related('species', 'enclosure', 'owner')
        outside_animals_needing_feed = outside_animals_qs.filter(Q(last_fed_at__lt=threshold) | Q(last_fed_at__isnull=True))

        outside_cleaning_enclosures = outside_enclosures.filter(Q(last_cleaned_at__lt=clean_threshold) | Q(last_cleaned_at__isnull=True))

        # Mark whether outside tasks are unassigned (no StaffRole on enclosure)
        outside_animal_tasks = []
        for a in outside_animals_needing_feed:
            is_unassigned = not StaffRole.objects.filter(enclosure=a.enclosure).exists()
            outside_animal_tasks.append({
                'animal': a,
                'enclosure': a.enclosure,
                'is_unassigned': is_unassigned,
                'can_feed': can_feed_animal(user, a) or (user.is_staff and is_unassigned),
            })

        outside_cleaning_tasks = []
        for e in outside_cleaning_enclosures:
            is_unassigned = not StaffRole.objects.filter(enclosure=e).exists()
            # role for the current user on this enclosure (likely None for outside)
            role_for_user = StaffRole.objects.filter(user=user, enclosure=e).first()
            can_clean = user.is_staff or (role_for_user and role_for_user.can_clean_enclosure())
            # allow staff to clean unassigned enclosures
            if is_unassigned and user.is_staff:
                can_clean = True
            outside_cleaning_tasks.append({
                'enclosure': e,
                'is_unassigned': is_unassigned,
                'can_clean': can_clean,
            })

        ctx['outside_animal_tasks'] = outside_animal_tasks
        ctx['outside_cleaning_tasks'] = outside_cleaning_tasks

        # expose the assigned enclosures and roles
        ctx['enclosures'] = enclosures
        ctx['user_roles'] = get_user_staff_roles(user)

        return ctx

