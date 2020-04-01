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
	def __init__(self, name, fips, population):
		# geographical data
		self.name = name
		self.fips = fips
		self.population = population
		self.sub_regions = {}
		self.sub_regions_names = {}

		# COVID-19 data
		self.cases = {}
		self.latest_cases = 0
		self.deaths = {}
		self.latest_deaths = 0
		self.latest_date = None

	def __eq__(self, other):
		return self.name == other.name

	def __str__(self):
		if not self.latest_date:
			return '{} ({}, pop {})'.format(self.name,
				self.fips,
				self.population)
		return '{} ({}, pop {}): {}, {} ({})'.format(self.name,
			self.fips,
			self.population,
			self.latest_cases,
			self.latest_deaths,
			self.latest_date.date())

	def __repr__(self):
		return self.__str__()

	############ SETTERS / GETTERS ############

	def get_fips(self):
		return self.fips

	def get_sub_regions(self):
		return self.sub_regions_names

	def add_sub_region(self, name, fips, population):
		self.sub_regions[int(fips)] = Region(name, fips, population)
		self.sub_regions_names[name] = self.sub_regions[int(fips)]
		return self.sub_regions[int(fips)]

	def return_sub_region(self, fips):
		fips = int(fips)
		if fips in self.sub_regions:
			return self.sub_regions[fips]
		return None

	############ CASES ############

	def update_cases(self, date, number):
		self.cases[date] = int(number)
		date_obj = DateUtil.parse_date(date)
		self.latest_cases = max(self.latest_cases, int(number))
		if not self.latest_date or date_obj > self.latest_date:
			self.latest_date = date_obj

	def get_cases(self, date = None, per_capita = True):
		if date and date not in self.cases:
			return None
		if date:
			return self.cases[date] / self.population * per_capita if per_capita else self.cases[date]
		return self.cases

	def get_latest_cases(self, per_capita = True):
		return self.latest_cases / self.population * per_capita if per_capita else self.latest_cases

	############ DEATHS ############

	def update_deaths(self, date, number):
		self.deaths[date] = int(number)
		date_obj = DateUtil.parse_date(date)
		self.latest_deaths = max(self.latest_deaths, int(number))
		if not self.latest_date or date_obj > self.latest_date:
			self.latest_date = date_obj

	def get_deaths(self, date = None, per_capita = True):
		if date and date not in self.deaths:
			return None
		if date:
			return self.deaths[date] * per_capita / self.population if per_capita else self.deaths[date]
		return self.deaths

	def get_latest_deaths(self, per_capita = True):
		return self.latest_deaths * per_capita / self.population if per_capita else self.latest_deaths

	############ PLOT CASES ############

	def plot_cases(self, start_date, end_date = None, legend = None, labels = True, per_capita = True):
		if not end_date:
			if not self.latest_date:
				return
			end_date = str(self.latest_date.date())
		dates = DateUtil.get_date_range(start_date, end_date)
		DateUtil.set_date_axes()

		cases = [self.get_cases(str(date), per_capita = per_capita) for date in dates]
		plt.plot(dates, cases, label = legend if legend else self.name)
		if labels:
			regex = " {:.2f}" if per_capita else " {:.0f}"
			plt.text(dates[-1], cases[-1], regex.format(cases[-1]), verticalalignment = 'center')

	def plot_sub_regions_cases(self, start_date, end_date = None, sec = None, labels = True, per_capita = True):
		most_cases = list(self.sub_regions.values())
		most_cases.sort(key = lambda r: r.get_latest_cases(per_capita), reverse = True)
		if not sec:
			sec = slice(0, min(20, len(most_cases)))

		for sub_region in most_cases[sec]:
			sub_region.plot_cases(start_date, end_date, labels = labels, per_capita = per_capita)

		self.plot_setup(per_capita, "Cases")

	############ PLOT DEATHS ############

	def plot_deaths(self, start_date, end_date = None, legend = None, labels = True, per_capita = True):
		if not end_date:
			if not self.latest_date:
				return
			end_date = str(self.latest_date.date())
		dates = DateUtil.get_date_range(start_date, end_date)
		DateUtil.set_date_axes()

		deaths = [self.get_deaths(str(date), per_capita = per_capita) for date in dates]
		plt.plot(dates, deaths, label = legend if legend else self.name)
		if labels:
			regex = " {:.2f}" if per_capita else " {:.0f}"
			plt.text(dates[-1], deaths[-1], regex.format(deaths[-1]), verticalalignment = 'center')

	def plot_sub_regions_deaths(self, start_date, end_date = None, sec = None, labels = True, per_capita = True):
		most_deaths = list(self.sub_regions.values())
		most_deaths.sort(key = lambda r: r.get_latest_deaths(per_capita), reverse = True)
		if not sec:
			sec = slice(0, min(20, len(most_deaths)))

		for sub_region in most_deaths[sec]:
			sub_region.plot_deaths(start_date, end_date, labels = labels, per_capita = per_capita)

		self.plot_setup(per_capita, "Deaths")

	def plot_cases_vs_deaths(self, start_date, end_date = None, labels = True, per_capita = True):
		if not end_date:
			if not self.latest_date:
				return
			end_date = str(self.latest_date.date())
		self.plot_cases(start_date, end_date, legend = 'Cases', labels = labels, per_capita = per_capita)
		self.plot_deaths(start_date, end_date, legend = 'Deaths', labels = labels, per_capita = per_capita)

		self.plot_setup(per_capita)

	def plot_setup(self, per_capita, category = None):
		ax = plt.gca()
		ax.spines['right'].set_visible(False)
		ax.spines['top'].set_visible(False)

		plt.xlabel("Date")
		ylabel = "Cumulative Number" + (" of " + category if category else "") + (" (Per " + '{:,}'.format(per_capita) + ")" if per_capita else "")
		plt.ylabel(ylabel)
		title = "COVID-19 " + (category if category else "Cases and Deaths") + (" Per " + '{:,}'.format(per_capita) if per_capita else "") + " in " + self.name
		plt.suptitle(title, y = 0.985, fontsize = 14)
		subtitle = "Total: "
		if not category:
			subtitle += '{:,}'.format(self.latest_cases) + " Cases, " + '{:,}'.format(self.latest_deaths) + " Deaths"
		if category == "Cases":
			subtitle += '{:,}'.format(self.latest_cases)
		if category == "Deaths":
			subtitle += '{:,}'.format(self.latest_deaths)
		plt.title(subtitle, fontsize = 10)
		plt.legend()
		plt.tight_layout(pad = 1)
		plt.show()

def get_us_population():
	request_url = "https://api.census.gov/data/2019/pep/population?get=POP&for=us:*"
	data = requests.get(request_url).json()
	population = data[1][0]
	return population

def get_state_populations():
	request_url = "https://api.census.gov/data/2019/pep/population?get=NAME,POP&for=state:*"
	populations = requests.get(request_url).json()
	return populations[1:]

def get_county_populations():
	request_url = "https://api.census.gov/data/2019/pep/population?get=NAME,POP&for=county:*&in=state:*"
	populations = requests.get(request_url).json()
	return populations[1:]

def setup_regions():
	US = create_us_region()
	add_state_regions(US)
	add_county_regions(US)
	return US, US.get_sub_regions()

def create_us_region():
	population = get_us_population()
	US = Region("USA", None, int(population))
	return US

def add_state_regions(US):
	populations = get_state_populations()
	for name, population, fips in populations:
		US.add_sub_region(name, fips, int(population))
	return US.get_sub_regions()

def add_county_regions(US):
	populations = get_county_populations()
	new_york_city_population = 0
	for name, population, state_fips, fips in populations:
		total_fips = state_fips + fips
		if int(total_fips) in (36061, 36047, 36081, 36005, 36085):
			new_york_city_population += int(population)
			continue
		name = ''.join(name.split(',')[:-1])
		name = ' '. join(name.split()[:-1])
		state = US.return_sub_region(state_fips)
		if state:
			state.add_sub_region(name, total_fips, int(population))
	US.return_sub_region(36).add_sub_region("New York City", "36061", new_york_city_population)
	return US.get_sub_regions()

def parse_us_states(filename, US):
	data_file = open(filename)
	reader = csv.reader(data_file)
	next(reader)
	for row in reader:
		date, state, fips, cases, deaths = row
		US.update_cases(date, int(cases) if US.get_cases(date) == None 
			else (US.get_cases(date, per_capita = False) + int(cases)))
		US.update_deaths(date, int(deaths) if US.get_deaths(date) == None 
			else US.get_deaths(date, per_capita = False) + int(deaths))
		state = US.return_sub_region(fips)
		if state:
			state.update_cases(date, cases)
			state.update_deaths(date, deaths)
	return US

def parse_us_counties(filename, US):
	data_file = open(filename)
	reader = csv.reader(data_file)
	next(reader)
	for row in reader:
		date, county, state, fips, cases, deaths = row
		if county == "New York City":
			fips = "36061"
		if not fips:
			continue
		state_fips = int(fips) // 1000
		state = US.return_sub_region(state_fips)
		if not state:
			continue
		county = state.return_sub_region(fips)
		if county:
			county.update_cases(date, cases)
			county.update_deaths(date, deaths)

# read in data
US, states = setup_regions()
parse_us_states('us-states.csv', US)
parse_us_counties('us-counties.csv', US)

# plot US data
US.plot_cases_vs_deaths('2020-03-01', per_capita = 10000)
US.plot_sub_regions_cases('2020-03-01', per_capita = 10000)
US.plot_sub_regions_cases('2020-03-01', sec = slice(2, 22), per_capita = 10000)
US.plot_sub_regions_deaths('2020-03-01', sec = slice(1, 21), per_capita = False)

# plot state data
states["Massachusetts"].plot_sub_regions_cases('2020-03-01', per_capita = 10000)
states["Massachusetts"].plot_sub_regions_deaths('2020-03-16', per_capita = False)
states["California"].plot_sub_regions_cases('2020-03-01', per_capita = 10000)
states["Illinois"].plot_sub_regions_cases('2020-03-01', per_capita = 10000)
states["Utah"].plot_sub_regions_cases('2020-03-01', per_capita = 10000)
states["New York"].plot_sub_regions_cases('2020-03-01', per_capita = 10000)
