from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Job(models.Model):
	name = models.CharField(max_length=100)
	address = models.CharField(max_length=200)
	created_at = models.DateTimeField(auto_now_add=True)
	user = models.ForeignKey(User, on_delete=models.CASCADE)

	def display_name(self):
		return self.name if self.name else self.address

	def __str__(self):
		return self.display_name()

class TimeEntry(models.Model):
	BREAK_CHOICES = [
		(0, 'No break'),
		(30, '30 minutes'),
		(60, '60 minutes'),
	]
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	job = models.ForeignKey(Job, on_delete=models.CASCADE)
	date = models.DateField()
	start_time = models.TimeField()
	end_time = models.TimeField()
	break_duration = models.IntegerField(choices=BREAK_CHOICES, default=0)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def total_hours(self):
		from datetime import datetime, timedelta
		start = datetime.combine(self.date, self.start_time)
		end = datetime.combine(self.date, self.end_time)
		duration = (end - start) - timedelta(minutes=self.break_duration)
		return round(duration.total_seconds() / 3600, 2)

	def __str__(self):
		return f"{self.date} | {self.job.display_name()} | {self.total_hours()} hrs"

	class Meta:
		unique_together = ('user', 'date', 'start_time')
