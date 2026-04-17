from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from .models import Conference
from .forms import ConferenceForm
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
import re
from datetime import datetime
from .scraper import scrape_university_sync

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
        conference.delete()
        messages.success(request, f'Conference "{conference.name}" has been deleted successfully.')
        return redirect('conference_list') 
    
    context = {'conference': conference}
    return render(request, 'conferences/delete.html', context)


@login_required
def scraping_page(request):
    # Get last 5 conferences from database
    recent_conferences = Conference.objects.all().order_by('-id')[:5]
    return render(request, 'conferences/scraping.html', {
        'recent_conferences': recent_conferences
    })



@csrf_protect
@login_required  # Added login_required
def start_scraping(request):
    """Handle the scraping form submission - EXTRACTS MULTIPLE CONFERENCES"""
    if request.method != 'POST':
        return redirect('dashboard')  
    
    url = request.POST.get('university_url', '').strip()
    
    if not url:
        messages.error(request, 'Please enter a valid URL')
        return redirect('scraping_page')  
    
    # Validate URL format
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    try:
        messages.info(request, f'Starting to scrape: {url}')
        
        # Run the scraper
        result = scrape_university_sync(url)
        
        if result['status'] == 'success':
            # Store as LIST for multiple conference support
            # Even if only one found, wrap it in a list
            conference_data = result['data']
            
            # If data is a single dict, convert to list
            if isinstance(conference_data, dict):
                conferences_list = [conference_data]
            else:
                conferences_list = conference_data  # Already a list
            
            # Store in session as LIST (key change!)
            request.session['scraped_conferences'] = conferences_list
            request.session['scraped_url'] = url
            request.session['debug_markdown'] = result.get('raw_markdown', '')
            
            # Clear old single conference data
            if 'scraped_data' in request.session:
                del request.session['scraped_data']
            
            messages.success(request, f'Found {len(conferences_list)} conference(s)! Review the extracted information.')
            return redirect('scraping_results')
        else:
            messages.error(request, f"Scraping failed: {result.get('message', 'Unknown error')}")
            return redirect('scraping_page')
            
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('scraping_page')


@login_required  # Added login_required
def scraping_results(request):
    """Display multiple conferences found - USER SELECTS ONE"""
    conferences = request.session.get('scraped_conferences', [])
    source_url = request.session.get('scraped_url', '')
    debug_content = request.session.get('debug_markdown', '')
    
    # Backwards compatibility
    if not conferences:
        single = request.session.get('scraped_data', {})
        if single:
            conferences = [single]
    
    if not conferences:
        messages.warning(request, 'No conferences found. Please submit a URL first.')
        return redirect('scraping_page')
    
    # Get selected conference index (if user clicked on one)
    selected_idx = request.GET.get('select')
    selected_conference = None
    
    if selected_idx is not None:
        try:
            idx = int(selected_idx)
            if 0 <= idx < len(conferences):
                selected_conference = conferences[idx]
        except (ValueError, IndexError):
            pass
    
    context = {
        'conferences': conferences,
        'conference': selected_conference,  # Single selected conference for detail view
        'source_url': source_url,
        'count': len(conferences),
        'selected_idx': selected_idx,
        'debug_mode': request.GET.get('debug') == '1',
        'raw_content': debug_content if request.GET.get('debug') == '1' else ''
    }
    
    return render(request, 'conferences/scraping_results.html', context)

@login_required
def save_conference(request):
    """Save selected conference to database and redirect to list"""
    if request.method != 'POST':
        messages.error(request, 'Invalid request')
        return redirect('scraping_results')
    
    idx = request.POST.get('conference_idx', '0')
    conferences = request.session.get('scraped_conferences', [])
    
    if not conferences:
        messages.error(request, 'No conference data found. Please scrape again.')
        return redirect('scraping_page')
    
    try:
        idx = int(idx)
        if idx < 0 or idx >= len(conferences):
            messages.error(request, 'Invalid conference selected')
            return redirect('scraping_results')
        
        data = conferences[idx]
        
        # Generate unique key
        key = (data.get('acronym') or 'CONF')[:10]
        if not key or key.strip() == '':
            key = 'CONF2026'
        
        # Make key unique
        original_key = key
        counter = 1
        while Conference.objects.filter(key=key).exists():
            key = f"{original_key[:8]}{counter}"
            counter += 1
        
        # PARSE DATE to YYYY-MM-DD format
        date_str = data.get('dates', '')
        parsed_date = None
        
        if date_str and date_str != 'TBD':
            try:
                # Try patterns like "May 12-14, 2026" or "May 12, 2026"
                # Extract year, month, day
                year_match = re.search(r'20\d{2}', date_str)
                if year_match:
                    year = year_match.group(0)
                    
                    # Map month names to numbers
                    months = {
                        'january': 1, 'february': 2, 'march': 3, 'april': 4,
                        'may': 5, 'june': 6, 'july': 7, 'august': 8,
                        'september': 9, 'october': 10, 'november': 11, 'december': 12
                    }
                    
                    month_num = None
                    month_match = re.search(r'(january|february|march|april|may|june|july|august|september|october|november|december)', date_str, re.IGNORECASE)
                    if month_match:
                        month_num = months.get(month_match.group(0).lower())
                    
                    if month_num:
                        # Get first day number found
                        day_match = re.search(r'\b(\d{1,2})\b', date_str)
                        day = int(day_match.group(1)) if day_match else 1
                        parsed_date = f"{year}-{month_num:02d}-{day:02d}"
            except:
                parsed_date = None
        
        # If no valid date, use today's date or None based on your model
        if not parsed_date:
            # Option: Use None if your model allows null
            parsed_date = None
            
            # Option: Use a default date (uncomment if your model requires a date)
            # from django.utils import timezone
            # parsed_date = timezone.now().date()
        
        # Create Conference
        conf = Conference.objects.create(
            name=data.get('conference_name', 'Unknown Conference')[:200],
            key=key,
            domain=', '.join(data.get('topics', ['Computer Science', 'AI'])[:3]),
            date=parsed_date,
            location=data.get('location', 'Algeria')[:100],
            audience="international" if 'international' in str(data.get('conference_name', '')).lower() else "national",
            acts=bool(data.get('submission_deadline'))
        )
        
        messages.success(request, f'✅ Conference "{conf.name}" saved successfully!')
        return redirect('conference_list')  
        
    except Exception as e:
        messages.error(request, f'Error saving: {str(e)}')
        return redirect('scraping_results')
