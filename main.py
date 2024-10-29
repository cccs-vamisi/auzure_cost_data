
import os
import json
import asyncio
from azure.identity import DefaultAzureCredential
from azure.mgmt.costmanagement import CostManagementClient
from azure.mgmt.costmanagement.models import QueryDefinition, QueryDataset, QueryTimePeriod, QueryAggregation, QueryGrouping
from datetime import datetime, timedelta, timezone
import openpyxl
from openpyxl import Workbook, load_workbook
from dateutil.relativedelta import relativedelta 

print(f"Welcome to my program {os.getlogin()}! This program collects Azure resource cost data for you" + "\n"+
      "and sends it to an Excel sheet")
print("Open a separate terminal and run the following command: pip install azure-mgmt-costmanagement azure-identity openpyxl")
print("***********************")
print("***********************")

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

# The following code will calculate the time frame for the last 3 months
start_date_for_last_three_months = datetime.now() - relativedelta(months=3)
end_date_for_last_three_months = datetime.now()

# The following code will calculate the time frame for the last 1 month
start_date_for_last_one_month = datetime.now() - relativedelta(months=1)
end_date_for_last_one_month = datetime.now()


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

    async def fetch_cost_for_last_twelve_months(self):
        return self.helper_method(start_date_of_last_twelve_months, end_date_of_last_twelve_months, self.scope).rows
    
    async def fetch_cost_for_the_current_year(self):
        return self.helper_method(start_date_for_current_year, end_date_for_current_year, self.scope).rows
        
    async def fetch_cost_for_last_three_months(self):
        return self.helper_method(start_date_for_last_three_months, end_date_for_last_three_months, self.scope).rows

    async def fetch_cost_for_last_month(self):
        return self.helper_method(start_date_for_last_one_month, end_date_for_last_one_month, self.scope).rows
    

resource_group = ""
subscription_id = ""
scope = ""
async def main_method():
    global resource_group
    global subscription_id
    global scope
    valid_answers = True
    while(valid_answers):
        resource_group = input("type in your resource group and press enter: ")
        subscription_id = input("type in your subscription id and press enter: ")
        resource_group = resource_group.replace('"', '').strip()
        resource_group = resource_group.replace("'", '')
        
        subscription_id = subscription_id.replace('"', '').strip()
        subscription_id = subscription_id.replace("'", '')
        
        if(len(resource_group) == 0 or len(subscription_id) == 0):
            print("Please follow the the instructions")
        else:
            valid_answers = False
            scope = f'/subscriptions/{subscription_id}/resourceGroups/{resource_group}'
            obj = Data(resource_group, subscription_id, scope)
            task1 = asyncio.create_task(obj.fetch_cost_for_last_twelve_months())
            task2 = asyncio.create_task(obj.fetch_cost_for_the_current_year())
            task3 = asyncio.create_task(obj.fetch_cost_for_last_three_months())
            task4 = asyncio.create_task(obj.fetch_cost_for_last_month())

            obj.final_returned_data["twelve"] = await task1
            obj.final_returned_data["current_year"] = await task2
            obj.final_returned_data["three"] = await task3
            obj.final_returned_data["one"] = await task4
            print(json.dumps(obj.final_returned_data, indent=4))



asyncio.run(main_method())






