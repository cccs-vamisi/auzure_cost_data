
import os
from azure.identity import DefaultAzureCredential
from azure.mgmt.costmanagement import CostManagementClient
from azure.mgmt.costmanagement.models import QueryDefinition, QueryDataset, QueryTimePeriod, QueryAggregation, QueryGrouping
from datetime import datetime, timedelta, timezone
import openpyxl
from dateutil.relativedelta import relativedelta 

print(f"Welcome to my program {os.getlogin()}! This program collects Azure resource cost data for you" + "\n"+
      "and sends it to an Excel sheet")
print("Open a separate terminal and run the following command: pip install azure-mgmt-costmanagement azure-identity openpyxl")

# Initialize the Azure Cost Management client with authentication:
credential = DefaultAzureCredential()
client = CostManagementClient(credential)


# The following code will calculate the time frame for the last 12 months
start_date_of_last_twelve_months = datetime.now() - relativedelta(months=12)
end_date_of_last_twelve_months = datetime.today().replace(day=1) - timedelta(days=1)


# The following code will calculate the time frame for the current year
current_year = datetime.now().year
start_date_for_current_year = datetime(current_year, 1, 1) 
end_date_for_current_year = datetime.now()

# The following code will calculate the time frame for the last 6 months
start_date_for_last_six_months = datetime.now() - relativedelta(months=6)
end_date_for_last_six_months = datetime.now()

# The following code will calculate the time frame for the last 3 months
start_date_for_last_three_months = datetime.now() - relativedelta(months=3)
end_date_for_last_three_months = datetime.now()

# The following code will calculate the time frame for the last 1 month
start_date_for_last_one_month = datetime.now() - relativedelta(months=1)
end_date_for_last_one_month = datetime.now()

# The following code will calculate the time frame for the last week
start_date_for_last_week = datetime.now() - relativedelta(days=6)
end_date_for_last_week = datetime.now()

# The following will contain the data that will be sent to an Excel sheet



# This class will contain the main methods to get the data
class Data():
    def __init__(self, resource_group, subscription_id, scope, final_returned_data=dict()):
        self.resource_group = resource_group
        self.subscription_id = subscription_id
        self.scope = scope
        self.final_returned_data = final_returned_data
        
    def helper_method(self, from_date, to_date, scope_value):
        time_period=QueryTimePeriod(from_property=from_date, to=to_date)
        query_aggregation = dict()
        query_aggregation["totalCost"] = QueryAggregation(name="Cost", function="Sum")
        querydataset = QueryDataset(granularity="Monthly", configuration=None, aggregation=query_aggregation)
        query = QueryDefinition(type="ActualCost", timeframe="Custom", time_period=time_period, dataset=querydataset)
        result = client.query.usage(scope = scope_value, parameters=query)
        return result

    def fetch_cost_for_last_twelve_months(self):
        returned_data = self.helper_method(start_date_of_last_twelve_months, end_date_of_last_twelve_months, self.scope)
        self.final_returned_data["twelve"] = returned_data.rows
    
    def fetch_cost_for_the_current_year(self):
        returned_data = self.helper_method(start_date_for_current_year, end_date_for_current_year, self.scope)
        self.final_returned_data["current_year"] = returned_data.rows
    
    def fetch_cost_for_last_six_months(self):
        returned_data = self.helper_method(start_date_for_last_six_months, end_date_for_last_six_months, self.scope)
        self.final_returned_data["six"] = returned_data.rows
    
    
    def fetch_cost_for_last_three_months(self):
        returned_data = self.helper_method(start_date_for_last_three_months, end_date_for_last_three_months, self.scope)
        self.final_returned_data["three"] = returned_data.rows
    
    def fetch_cost_for_last_month(self):
        returned_data = self.helper_method(start_date_for_last_one_month, end_date_for_last_one_month, self.scope)
        self.final_returned_data["one"] = returned_data.rows
    
    def fetch_cost_for_last_week(self):
        returned_data = self.helper_method(start_date_for_last_week, end_date_for_last_week, self.scope)
        self.final_returned_data["week"] = returned_data.rows

resource_group = "AnalyticalPlatformPilot"
subscription_id = "3d352af3-d439-4244-8519-74bdf2d926b5"
scope = f'/subscriptions/{subscription_id}/resourceGroups/{resource_group}'
obj = Data("AnalyticalPlatformPilot", "3d352af3-d439-4244-8519-74bdf2d926b5", scope)
obj.fetch_cost_for_the_current_year()
print(obj.final_returned_data["current_year"])








