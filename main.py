
import os
import json
import asyncio
from azure.core.exceptions import HttpResponseError
from azure.identity import DefaultAzureCredential
from azure.mgmt.costmanagement import CostManagementClient
from azure.mgmt.costmanagement.models import QueryDefinition, QueryDataset, QueryTimePeriod, QueryAggregation, QueryGrouping
from datetime import datetime, timedelta, timezone
from openpyxl import Workbook, load_workbook
from dateutil.relativedelta import relativedelta 
import time

print(f"Welcome to my program {os.getlogin()}! This program collects Azure resource cost data for you" + "\n"+
      "and sends it to an Excel sheet")
print("Make sure you read the readme file before executing the code")
print("***********************")
print("***********************")

# Initialize the Azure Cost Management client with authentication:
credential = DefaultAzureCredential()
client = CostManagementClient(credential)

current_date =  datetime.now()
# The following code will calculate the time frame for the last 12 months
start_date_of_last_twelve_months = (current_date.replace(day=1) - relativedelta(months=1)).replace(day=1) - relativedelta(months=11)
end_date_of_last_twelve_months = current_date.replace(day=1) - timedelta(days=1)

# The following code will calculate the time frame for the current year
current_year = current_date.year
start_date_for_current_year = datetime(current_year, 1, 1) 
end_date_for_current_year = current_date

# The following code will calculate the time frame for the last 3 months
start_date_for_last_three_months = (current_date.replace(day=1) - relativedelta(months=1)).replace(day=1) - relativedelta(months=2)
end_date_for_last_three_months = current_date.replace(day=1) - timedelta(days=1)

# The following code will calculate the time frame for the last 1 month
start_date_for_last_one_month = current_date.replace(day=1) - relativedelta(months=1)
end_date_for_last_one_month = current_date.replace(day=1) - timedelta(days=1)
# This class will contain the methods to get the data
class Data():
    
    def __init__(self, resource_group, 
                 subscription_id, 
                 scope, 
                 final_returned_data=dict()):
        self.resource_group = resource_group
        self.subscription_id = subscription_id
        self.scope = scope
        self.final_returned_data = final_returned_data
        
    # This helper method will help remove repetitive code
    def helper_method(self, from_date, to_date, scope_value):
        time_period=QueryTimePeriod(from_property=from_date, to=to_date)
        query_aggregation = dict()
        query_aggregation["totalCost"] = QueryAggregation(name="Cost", function="Sum")
        querydataset = QueryDataset(granularity="Monthly", configuration=None, aggregation=query_aggregation)
        query = QueryDefinition(type="ActualCost", timeframe="Custom", time_period=time_period, dataset=querydataset)
        while True:
            try:
                    # Make the API request
                    result = client.query.usage(scope=scope_value, parameters=query)
                    return result.rows
                
            except HttpResponseError as e:
                    # Check for rate-limiting headers
                    retry_after_qpu = int(e.response.headers.get('x-ms-ratelimit-microsoft.costmanagement-qpu-retry-after', 0))
                    retry_after_entity = int(e.response.headers.get('x-ms-ratelimit-microsoft.costmanagement-entity-retry-after', 0))
                    retry_after_tenant = int(e.response.headers.get('x-ms-ratelimit-microsoft.costmanagement-tenant-retry-after', 0))
                    retry_after_client = int(e.response.headers.get('x-ms-ratelimit-microsoft.costmanagement-client-retry-after', 0))
                    
                    # Determine the maximum retry time
                    max_retry_after = max(retry_after_qpu, retry_after_entity, retry_after_tenant, retry_after_client)
                    
                    if max_retry_after > 0:
                        print(f"Rate-limited. Retrying in {max_retry_after} seconds...")
                        time.sleep(max_retry_after)
                    else:
                        raise e  # Re-raise the exception if no retry headers are present
    
    async def fetch_cost_for_last_twelve_months(self):
        return self.helper_method(start_date_of_last_twelve_months, end_date_of_last_twelve_months, self.scope)
    
    async def fetch_cost_for_the_current_year(self):
        return self.helper_method(start_date_for_current_year, end_date_for_current_year, self.scope)
        
    async def fetch_cost_for_last_three_months(self):
        return self.helper_method(start_date_for_last_three_months, end_date_for_last_three_months, self.scope)

    async def fetch_cost_for_last_month(self):
        return self.helper_method(start_date_for_last_one_month, end_date_for_last_one_month, self.scope)
    

resource_group = ""
subscription_id = ""
scope = ""
async def main_method():
    global resource_group
    global subscription_id
    global scope
    keep_looping = True
    while(keep_looping):
        resource_group = input("type in your resource group and press enter: ")
        subscription_id = input("type in your subscription id and press enter: ")
        resource_group = resource_group.replace('"', '').replace("'", '').strip()
        subscription_id = subscription_id.replace('"', '').replace("'", '').strip()

        if(len(resource_group) == 0 or len(subscription_id) == 0):
            print("Please follow the the instructions!")
        else:
            # Async gather/ task group can also be used here...
            keep_looping = False
            scope = f'/subscriptions/{subscription_id}/resourceGroups/{resource_group}'
            obj = Data(resource_group, subscription_id, scope)
            task1 = asyncio.create_task(obj.fetch_cost_for_last_twelve_months())
            task2 = asyncio.create_task(obj.fetch_cost_for_the_current_year())
            task3 = asyncio.create_task(obj.fetch_cost_for_last_three_months())
            task4 = asyncio.create_task(obj.fetch_cost_for_last_month())


            obj.final_returned_data["last_twelve_months"] = await task1
            obj.final_returned_data["current_year"] = await task2
            obj.final_returned_data["last_three_months"] = await task3
            obj.final_returned_data["last_month"] = await task4
            return obj.final_returned_data

def format_data(data):
    for key in data.keys():
        list_item = data[key]
        
        for i in range(0, len(list_item)):
            date_str = list_item[i][1]
            date_obj = datetime.fromisoformat(date_str)
            list_item[i][1] = date_obj
    return data

def excel_sheet_creation(received_data):
    work_book = Workbook()
    work_sheet = work_book.active
    work_sheet.title = resource_group
    work_sheet['A1'] = resource_group
    work_sheet['B1'] = "Date"
    work_sheet['C1'] = "Price"
    work_sheet['D1'] = "CAD"
    
    #Create a list of all the date
    data_for_last_twelve_months = received_data["last_twelve_months"]

    date_list = []
    price_list = []
    total_price = sum(price_list)
    
    for i in range(0, len(data_for_last_twelve_months)):
        price_list.append(data_for_last_twelve_months[i][0])
        date_list.append(data_for_last_twelve_months[i][1])
    
    start_row = 2
    start_column = 2
    
    for i, value in enumerate(date_list):
        month = value.strftime("%B")
        year = value.strftime("%Y")
        work_sheet.cell(row=start_row+i, column=start_column, value=f"{month}, {year}")

    start_row = 2
    start_column = 3
    
    for i, value in enumerate(price_list):
        value = round(value, 2)
        work_sheet.cell(row=start_row+i, column=start_column, value=value)
        
    start_row = 2
    start_column = 4
    for i, value in enumerate(price_list):
        work_sheet.cell(row=start_row+i, column=start_column, value="CAD")

    work_book.save("azure_cost_data.xlsx")
unformatted_data = asyncio.run(main_method())
formatted_data = format_data(unformatted_data)
excel_sheet_creation(formatted_data)
print(json.dumps(formatted_data["last_twelve_months"], indent=4, default=str))






