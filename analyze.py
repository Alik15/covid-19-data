import csv
import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import requests


class DateUtil:
	def parse_date(date_str):
		return datetime.datetime.strptime(date_str, "%Y-%m-%d")

	def get_date_range(start_date, end_date):
		start_date_obj = DateUtil.parse_date(start_date)
		end_date_obj = DateUtil.parse_date(end_date)
		diff = end_date_obj - start_date_obj
		dates = [start_date_obj + datetime.timedelta(days = i) for i in range(diff.days + 1)]
		dates = [date.date() for date in dates]
		return dates

	def set_date_axes():
		ax = plt.gca()
		formatter = mdates.DateFormatter("%m-%d")
		ax.xaxis.set_major_formatter(formatter)
		locator = mdates.WeekdayLocator(byweekday = mdates.MO)
		ax.xaxis.set_major_locator(locator)

class Region:
	def __init__(self, name, fips):
		self.name = name
		self.fips = fips
		self.cases = {}
		self.latest_cases = 0
		self.deaths = {}
		self.latest_deaths = 0
		self.latest_date = None
		self.sub_regions = {}

	def __eq__(self, other):
		return self.name == other.name

	def __str__(self):
		return '{} ({}): {}, {} ({})'.format(self.name,
			self.fips,
			self.latest_cases,
			self.latest_deaths,
			self.latest_date.date())

	def __repr__(self):
		return self.__str__()

	def update_cases(self, date, number):
		self.cases[date] = int(number)
		date_obj = DateUtil.parse_date(date)
		self.latest_cases = max(self.latest_cases, int(number))
		if not self.latest_date or date_obj > self.latest_date:
			self.latest_date = date_obj

	def update_sub_regions_cases(self, name, date, number):
		if name in sub_regions:
			sub_regions[name].update_cases(date, number)

	def update_deaths(self, date, number):
		self.deaths[date] = int(number)
		date_obj = DateUtil.parse_date(date)
		self.latest_deaths = max(self.latest_deaths, int(number))
		if not self.latest_date or date_obj > self.latest_date:
			self.latest_date = date_obj

	def update_sub_regions_deaths(self, name, date, number):
		if name in sub_regions:
			sub_regions[name].update_deaths(date, number)

	def add_sub_region(self, name, fips):
		self.sub_regions[name] = Region(name, fips)
		return self.sub_regions[name]

	def return_sub_region(self, name, fips):
		if name in self.sub_regions:
			return self.sub_regions[name]
		return self.add_sub_region(name, fips)

	def get_sub_regions(self):
		return self.sub_regions

	def get_cases(self, date = None, scale = 1):
		if date:
			return self.cases[date] / scale if date in self.cases else None
		return self.cases

	def get_latest_cases(self, scale = 1):
		return self.latest_cases / scale

	def get_deaths(self, date = None, scale = 1):
		if date:
			return self.deaths[date] / scale if date in self.deaths else None
		return self.deaths

	def get_latest_deaths(self, scale = 1):
		return self.latest_deaths / scale if date in self.cases else None

	def plot_cases(self, start_date, end_date = None, legend = None, labels = True, scale = 1):
		if not end_date:
			end_date = str(self.latest_date.date())
		dates = DateUtil.get_date_range(start_date, end_date)
		DateUtil.set_date_axes()

		cases = [self.get_cases(str(date), scale = scale) for date in dates]
		plt.plot(dates, cases, label = legend if legend else self.name)
		if labels:
			regex = " {:.2e}" if scale != 1 else " {:.0f}"
			plt.text(dates[-1], cases[-1], regex.format(cases[-1]))

	def plot_sub_regions_cases(self, start_date, end_date = None, sec = None, labels = True, per_capita = True):
		if per_capita:
			populations = get_populations(self.fips)
		most_cases = self.sub_regions.values()
		most_cases = list(filter(lambda r: r.fips in populations if per_capita else True, most_cases))
		most_cases.sort(key = lambda r: r.get_latest_cases(populations[r.fips] if per_capita else 1), reverse = True)
		if not sec:
			sec = slice(0, min(20, len(most_cases)))

		for sub_region in most_cases[sec]:
			sub_region.plot_cases(start_date, end_date, labels = labels, scale = populations[sub_region.fips] if per_capita else 1)

		self.plot_setup(per_capita, "Cases")

	def plot_deaths(self, start_date, end_date = None, legend = None, labels = True, scale = 1):
		if not end_date:
			end_date = str(self.latest_date.date())
		dates = DateUtil.get_date_range(start_date, end_date)
		DateUtil.set_date_axes()

		deaths = [self.get_deaths(str(date), scale = scale) for date in dates]
		plt.plot(dates, deaths, label = legend if legend else self.name)
		if labels:
			regex = " {:.2e}" if scale != 1 else " {:.0f}"
			plt.text(dates[-1], deaths[-1], regex.format(deaths[-1]))

	def plot_sub_regions_deaths(self, start_date, end_date = None, sec = None, labels = True, per_capita = True):
		if per_capita:
			populations = get_populations(self.fips)
		most_deaths = self.sub_regions.values()
		most_deaths = list(filter(lambda r: r.fips in populations if per_capita else True, most_deaths))
		most_deaths.sort(key = lambda r: r.get_latest_cases(populations[r.fips] if per_capita else 1), reverse = True)

		if not sec:
			sec = slice(0, min(20, len(most_deaths)))

		for sub_region in most_deaths[sec]:
			sub_region.plot_deaths(start_date, end_date, labels = labels, scale = populations[sub_region.fips] if per_capita else 1)

		self.plot_setup(per_capita, "Deaths")

	# def plot_cases_vs_deaths(self, start_date, end_date = None, labels = True, per_capita = True):
	# 	if not end_date:
	# 		end_date = str(self.latest_date.date())
	# 	self.plot_cases(start_date, end_date, legend = 'Cases', labels = labels, per_capita = per_capita)
	# 	self.plot_deaths(start_date, end_date, legend = 'Deaths', labels = labels, per_capita = per_capita)

	# 	self.plot_setup(per_capita)

	def plot_setup(self, per_capita, category = None):
		ax = plt.gca()
		ax.spines['right'].set_visible(False)
		ax.spines['top'].set_visible(False)

		plt.xlabel("Date")
		ylabel = "Cumulative Number" + (" of " + category if category else "") + (" (Per Capita)" if per_capita else "")
		plt.ylabel(ylabel)
		title = "COVID-19 " + (category if category else "Cases and Deaths") + (" Per Capita" if per_capita else "") + " in " + self.name
		plt.suptitle(title, y = 0.985, fontsize = 14)
		subtitle = "Total: "
		if not category:
			subtitle += str(self.latest_cases) + " Cases , " + str(self.latest_deaths) + " Deaths"
		if category == "Cases":
			subtitle += str(self.latest_cases)
		if category == "Deaths":
			subtitle += str(self.latest_deaths)
		plt.title(subtitle, fontsize = 10)
		plt.legend()
		plt.tight_layout(pad = 1)
		plt.show()

def get_us_population():
	data = requests.get("https://api.census.gov/data/2019/pep/population?get=POP&for=us:*").json()
	return int(data[1][0])

def get_populations(fips):
	request_url = "https://api.census.gov/data/2019/pep/population?get=POP&for=state:*"
	if fips != None:
		request_url = "https://api.census.gov/data/2019/pep/population?get=POP&for=county:*&in=state:" + fips
	populations = requests.get(request_url).json()
	if fips != None:
		populations = [[row[0], row[1] + row[2]] for row in populations]
	print(populations)
	pop_map = {}
	for pop, fips in populations[1:]:
		pop_map[fips] = int(pop)
	return pop_map

def parse_us_states(filename):
	US = Region("USA", None)
	data_file = open(filename)
	reader = csv.reader(data_file)
	next(reader)
	for row in reader:
		date, state, fips, cases, deaths = row
		fips = "{:02d}".format(int(fips)) if len(fips) > 0 else None
		US.return_sub_region(state, fips).update_cases(date, cases)
		US.update_cases(date, cases if US.get_cases(date) == None 
			else US.get_cases(date) + int(cases))
		US.return_sub_region(state, fips).update_deaths(date, deaths)
		US.update_deaths(date, deaths if US.get_deaths(date) == None 
			else US.get_deaths(date) + int(deaths))
	return US

def parse_us_counties(filename, states):
	data_file = open(filename)
	reader = csv.reader(data_file)
	next(reader)
	for row in reader:
		date, county, state, fips, cases, deaths = row
		fips = "{:05d}".format(int(fips)) if len(fips) > 0 else None
		if state not in states:
			continue
		states[state].return_sub_region(county, fips).update_cases(date, cases)
		states[state].return_sub_region(county, fips).update_deaths(date, deaths)

# read in data
US = parse_us_states('us-states.csv')
states = US.get_sub_regions()
parse_us_counties('us-counties.csv', states)
