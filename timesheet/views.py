
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Job, TimeEntry
from .forms import TimeEntryForm, JobForm
from datetime import timedelta

@login_required
def dashboard(request):
	today = timezone.localdate()
	entries = TimeEntry.objects.filter(user=request.user, date=today)
	if request.method == 'POST':
		form = TimeEntryForm(request.POST, user=request.user)
		if form.is_valid():
			entry = form.save(commit=False)
			entry.user = request.user
			entry.save()
			messages.success(request, 'Time entry added!')
			return redirect('dashboard')
	else:
		form = TimeEntryForm(user=request.user)
	return render(request, 'dashboard.html', {'entries': entries, 'form': form})

@login_required
def daily_entry(request):
	date_str = request.GET.get('date')
	date = timezone.localdate() if not date_str else timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
	entries = TimeEntry.objects.filter(user=request.user, date=date)
	if request.method == 'POST':
		form = TimeEntryForm(request.POST, user=request.user)
		if form.is_valid():
			entry = form.save(commit=False)
			entry.user = request.user
			entry.save()
			messages.success(request, 'Time entry saved!')
			return redirect('daily_entry')
	else:
		form = TimeEntryForm(user=request.user)
	return render(request, 'daily_entry.html', {'entries': entries, 'form': form, 'date': date})

@login_required
def weekly_summary(request):
	today = timezone.localdate()
	week_start = today - timedelta(days=today.weekday())
	week_dates = [week_start + timedelta(days=i) for i in range(7)]
	entries = TimeEntry.objects.filter(user=request.user, date__range=[week_start, week_start + timedelta(days=6)])
	daily_totals = {d: sum(e.total_hours() for e in entries.filter(date=d)) for d in week_dates}
	weekly_total = sum(daily_totals.values())
	return render(request, 'weekly_summary.html', {'week_dates': week_dates, 'daily_totals': daily_totals, 'weekly_total': weekly_total, 'entries': entries})

@login_required
def job_list(request):
	jobs = Job.objects.filter(user=request.user)
	return render(request, 'job_list.html', {'jobs': jobs})

@login_required
def job_create(request):
	if request.method == 'POST':
		form = JobForm(request.POST)
		if form.is_valid():
			job = form.save(commit=False)
			job.user = request.user
			job.save()
			messages.success(request, 'Job created!')
			return redirect('job_list')
	else:
		form = JobForm()
	return render(request, 'job_form.html', {'form': form})

@login_required
def job_edit(request, pk):
	job = get_object_or_404(Job, pk=pk, user=request.user)
	if request.method == 'POST':
		form = JobForm(request.POST, instance=job)
		if form.is_valid():
			form.save()
			messages.success(request, 'Job updated!')
			return redirect('job_list')
	else:
		form = JobForm(instance=job)
	return render(request, 'job_form.html', {'form': form, 'job': job})
