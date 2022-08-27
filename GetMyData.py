#!/usr/bin/python

import myfitnesspal, datetime, csv, sys, getopt
import pprint, json
import browser_cookie3
# from http.cookiejar import CookieJar

# Settings
bmr = 0
today = datetime.date.today()
latest_backup = False
macros = False
append_file = False
totals = False
water = False
user = ""
cookie_file = 'browser_cookie3/Default/Cookies'

# Read Startup Parameters
def usage():
    print("Usage:", __file__)
    print("\t-b <bmr>  : calculate total calorites and BMR percentage (default is none).")
    print("\t-c <file> : provide the cookie file that needs to be used (chrome only)")
    print("\t-d <date> : the first Date to extract YYYYMMDD.")
    print("\t-g <days> : number of days to Go back (default is 7 days).")
    print("\t-A        : Append file, takes last date from current file. (ignore -d -g)")
    print("\t-m        : extract Nacro data - fat, protein and carbs (defaults is none).")
    print("\t-w        : extract Water data from output *default is none).")

try:
    opts, args = getopt.getopt(sys.argv[1:], "wmhTAc:b:d:g:", ["help", "totals", "water", "macros", "append", "daysback=", "cookie_file=", "bmr=", "date="])
    for opt, arg in opts:
        if opt in ("-h", "help"):
            raise ValueError("Command line options")
        elif opt in ("-g", "--daysback"):
            latest_backup = today - datetime.timedelta(days=int(arg))
        elif opt in ("-d", "--date"):
            latest_backup = datetime.datetime.strptime(arg, '%Y%m%d').date()
        elif opt in ("-c", "--cookie_file"):
            cookie_file = arg
        elif opt in ("-A", "--append"):
            append_file = True
        elif opt in ("-T", "--totals"):
            totals = True
        elif opt in ("-b", "--bmr"):
            bmr = int(arg)
        elif opt in ("-w", "--water"):
            water = True
        elif opt in ("-m", "--macros"):
            macros = True
except Exception as e:
    print("%s" % e)
    usage()
    sys.exit()

if append_file:
    file_mode='a'
    with open('food.csv', 'r') as f:
        last_date = f.readlines()[-1].split(",")[0]
        latest_backup = datetime.datetime.strptime(last_date, '%Y-%m-%d').date()
        latest_backup += datetime.timedelta(days=1)
else:
    file_mode='w'

if latest_backup is False:
    print("No start date.")
    usage()
    sys.exit()

# create a local cookie file using MSF
# 
cj = browser_cookie3.chrome(cookie_file=cookie_file)
client = myfitnesspal.Client(cookiejar=cj)
# Will be reading from a username.login file, which is essentially a text file with the relevant info
# weight = client.get_measurements('Weight')
# print(json.dumps(weight))
# # keys, values = [], []
# for key, value in weight.items():
#     print(key,value)
# #     keys.append(key)
# #     values.append(value)       

# # with open("weight.csv", "w") as outfile:
# #     csvwriter = csv.writer(outfile)
# #     csvwriter.writerow(keys)
# #     csvwriter.writerow(values)

if totals:
    total_file = open('totals.csv', file_mode, newline='')
    total_writer = csv.writer(total_file)
    if file_mode == 'w':
        row = ["Date", "DayOfWeek", "fitness", "garmin", "breakfast", "lunch", "dinner", "snacks", "feest"]
        total_writer.writerow(row)

# Function to calculate date range. From somewhere on StackOverflow
def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + datetime.timedelta(n)

with open('food.csv', file_mode, newline='') as csv_file:
    days = 0
    writer = csv.writer(csv_file)
    if file_mode == 'w':
        row = ["Date", "DayOfWeek", "Type", "Description", "Calories", "Details"]
        writer.writerow(row)
    for date in daterange(latest_backup, today):
        pro = 0
        fat = 0
        car = 0
        gramstotal = 0
        total_exe_day = 0
        total_fit_day = 0
        total_cal_day = 0
        total_feest = 0
        total_breakfast = 0
        total_dinner = 0
        total_lunch = 0
        total_snacks = 0
        print("Request:", date)
        day = client.get_date(date)
        for meal_index in range(len(day.keys())):
            meal_time = day.keys()[meal_index]
            for ingredient_index in range(len(day.meals[meal_index].entries)):
                ingredient = day.meals[meal_index].entries[ingredient_index].get_as_dict()
                row = [date, date.strftime('%A'), meal_time, ingredient['name'], int(ingredient['nutrition_information']['calories']), str(ingredient['nutrition_information'])]
                writer.writerow(row)
                pro = pro + int(ingredient['nutrition_information']['carbohydrates'])
                fat = fat + int(ingredient['nutrition_information']['fat'])
                car = car + int(ingredient['nutrition_information']['protein'])
                total_cal_day = total_cal_day + int(ingredient['nutrition_information']['calories'])
                if meal_time == "feest":
                    total_feest = total_feest + int(ingredient['nutrition_information']['calories'])
                if meal_time == "lunch":
                    total_lunch = total_lunch + int(ingredient['nutrition_information']['calories'])
                if meal_time == "dinner":
                    total_dinner = total_dinner + int(ingredient['nutrition_information']['calories'])
                if meal_time == "breakfast":
                    total_breakfast = total_breakfast + int(ingredient['nutrition_information']['calories'])
                if meal_time == "snacks":
                    total_snacks = total_snacks + int(ingredient['nutrition_information']['calories'])           

        gramstotal = pro + fat + car
        #
        # As soon as data is not logged exit
        # if gramstotal == 0:
        #     break
        days = days + 1

        for exe_index in range(len(day.exercises[0].get_as_list())):
            exercise = day.exercises[0].get_as_list()[exe_index]
            row = [date, date.strftime('%A'), 'exercise', exercise['name'], int(exercise['nutrition_information']['calories burned']) * -1, str(exercise['nutrition_information'])]
            writer.writerow(row)
            # print(exercise['name'], exercise['nutrition_information'])
            if "adjustment" not in exercise['name']:
                total_fit_day = total_fit_day + int(exercise['nutrition_information']['calories burned'])
            total_exe_day = total_exe_day + int(exercise['nutrition_information']['calories burned'])

        try:            
            total =  total_exe_day - total_fit_day
            if total_exe_day != 0 or total_fit_day != 0:
                row = [date, date.strftime('%A'), 'total-garmin', 'Garmin Adjusted Excercise in kilocalories', total]
                writer.writerow(row)
            total =  (total_exe_day + bmr) - total_cal_day
            if bmr > 0 and total != 0:
                row = [date, date.strftime('%A'), 'total-bmr', 'Food and Excercise in kilocalories (' + 'percentage BMR ' + '{0:.0f}%'.format(total / bmr * 100) + ')', total]
                writer.writerow(row)
            total = total_cal_day - total_exe_day  
            if total_cal_day != 0 or total_exe_day != 0:
                row = [date, date.strftime('%A'), 'total-netcalories', 'Food and Exercise kilocalories', total]
                writer.writerow(row)
            if total_cal_day > 0:
                row = [date, date.strftime('%A'), 'total-calories', 'Food in kilocalories', total_cal_day, day.notes]
                writer.writerow(row)
            if total_fit_day > 0:
                row = [date, date.strftime('%A'), 'total-fitness', 'Total calories burned in fitness', total_fit_day]
                writer.writerow(row)
            if total_exe_day > 0:
                row = [date, date.strftime('%A'), 'total-exercise', 'Total calories burned', total_exe_day]
                writer.writerow(row)
            if total_feest > 0:
                row = [date, date.strftime('%A'), 'total-feest', 'Total calories party', total_feest]
                writer.writerow(row)
            if total_breakfast > 0:
                row = [date, date.strftime('%A'), 'total-breakfast', 'Total calories ontbijt', total_breakfast]
                writer.writerow(row)
            if total_lunch > 0:
                row = [date, date.strftime('%A'), 'total-lunch', 'Total calories lunch', total_lunch]
                writer.writerow(row)
            if total_dinner > 0:
                row = [date, date.strftime('%A'), 'total-dinner', 'Total calories dinner', total_dinner]
                writer.writerow(row)
            if total_snacks > 0:
                row = [date, date.strftime('%A'), 'total-snacks', 'Total calories snoep', total_snacks]
                writer.writerow(row)
                    
        except Exception as e:
            print(date, "Error: %s" % e)
            # row = [date, date.strftime('%A'), 'error', e]
            # writer.writerow(row)

        if totals:
            total_garmin =  total_exe_day - total_fit_day
            row = [date, date.strftime('%A'), total_fit_day, total_garmin, total_breakfast, total_lunch, total_dinner, total_snacks, total_feest]
            total_writer.writerow(row)

        if macros and gramstotal != 0:
            row = [date, date.strftime('%A'), 'total-carbs', 'Carbs in grams (' + '{0:.0f}%'.format(car / gramstotal * 100) + ') ', car]
            writer.writerow(row)
            row = [date, date.strftime('%A'), 'total-fat', 'Fat in grams (' + '{0:.0f}%'.format(fat / gramstotal * 100) + ') ', fat]
            writer.writerow(row)
            row = [date, date.strftime('%A'), 'total-protein', 'Protein in grams (' + '{0:.0f}%'.format(pro / gramstotal * 100) + ') ', pro]
            writer.writerow(row)
            

        if (water):
            if int(day.water) > 0:
                row = [date, date.strftime('%A'), 'total-water', 'Water in ml', int(day.water)]
                writer.writerow(row)

        # writer.writerow('')

    # row = ["", "", 'average', 'Calories consumed in ' + '{0:.0f}'.format(days) + ' days', int(total_cal / days)]
    # writer.writerow(row)
    # row = ["", "", 'average', 'Calories burned in ' + '{0:.0f}'.format(days) + ' days', int(total_exe / days)]
    # writer.writerow(row)
    # writer.writerow('')

    # overall = int((total_cal / days) - (total_exe / days))
    # row = ["", "", 'average', 'Maintained calories per day (percentage BMR ' + '{0:.0f}%'.format(overall / bmr * 100) + ')', overall]
    # writer.writerow(row)
