from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from .models import Conference
from .forms import ConferenceForm
from django.contrib import messages


@login_required
def conference_list(request):
    query = request.GET.get("q")
    if query:
        conferences = Conference.objects.filter(key__icontains=query)
    else:
        conferences = Conference.objects.all()
    return render(
        request,
        "conferences/list.html",
        {"conferences": conferences}
    )

@login_required
def conference_create(request):
    if request.method == "POST":
        # Generate a simple key from the name
        name = request.POST.get("name")
        key = name[:10].upper().replace(" ", "") if name else "CONF"
        
        Conference.objects.create(
            name=request.POST.get("name"),
            key=key,
            domain=request.POST.get("domain"),
            date=request.POST.get("date"),
            location=request.POST.get("location"),
            audience="national",  # Default value
            acts=False  # Default value
        )
        return redirect("conference_list")
    
    return render(request, "conferences/create.html")

@login_required
def annuler_conference(request, id):
    conference = Conference.objects.get(id=id)
    conference.annulee = True
    conference.save()
    return redirect("conference_list")
@login_required
def dashboard(request):
    conference_count = Conference.objects.count()
    return render(request, "conferences/dashboard.html", {
        "conference_count": conference_count
    })
@login_required
def conference_edit(request, id):
    conference = Conference.objects.get(id=id)
    if request.method == "POST":
        conference.name = request.POST.get("name")
        conference.domain = request.POST.get("domain")
        conference.date = request.POST.get("date")
        conference.location = request.POST.get("location")
        conference.audience = request.POST.get("audience", "national")
        conference.acts = request.POST.get("acts") == "on"
        conference.save()
        return redirect("conference_list")
    
    return render(request, "conferences/edit.html", {"conference": conference})

@login_required
def delete_conference(request, id):
    
    conference = get_object_or_404(Conference, id=id)
    
    if request.method == "POST":
        # Delete the conference
        conference.name = conference.name
        conference.delete()
        messages.success(request, f'Conference "{conference.name}" has been deleted successfully.')
        return redirect('conference_list') 
    
    #e
    context = {
        'conference': conference
    }
    return render(request, 'conferences/delete.html', context)

@login_required
def scraping_page(request):
    return render(request, 'conferences/scraping.html')

@login_required
def start_scraping(request):
    if request.method == 'POST':
        url = request.POST.get('university_url')
        scrape_conferences = request.POST.get('scrape_conferences') == 'on'
        scrape_faculties = request.POST.get('scrape_faculties') == 'on'
        deep_scan = request.POST.get('deep_scan') == 'on'
        
        # Validate URL
        if not url:
            messages.error(request, 'Please enter a valid URL')
            return redirect('scraping_page')
        
        # Here you would start your scraping logic
        # You could use Celery for background tasks
        # For now, just show a success message
        
        messages.success(request, f'Scraping started for {url}')
        return redirect('dashboard')
    
    return redirect('scraping_page')