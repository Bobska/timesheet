from django.contrib import admin
from .models import Job, TimeEntry

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
	list_display = ('name', 'address', 'user', 'created_at')
	search_fields = ('name', 'address', 'user__username')
	list_filter = ('user', 'created_at')

@admin.register(TimeEntry)
class TimeEntryAdmin(admin.ModelAdmin):
	list_display = ('user', 'job', 'date', 'start_time', 'end_time', 'break_duration', 'total_hours', 'created_at')
	search_fields = ('user__username', 'job__name', 'date')
	list_filter = ('user', 'job', 'date')
	readonly_fields = ('created_at', 'updated_at')

	def total_hours(self, obj):
		return obj.total_hours()
