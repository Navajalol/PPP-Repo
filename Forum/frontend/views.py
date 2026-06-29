from django.http import HttpResponse
from django.template import loader
import boto3
import time
import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import traceback

ATHENA_DATABASE = 'ppp_data'
ATHENA_OUTPUT = 's3://aws-s3-study-case/Paycheck-protection-program/Query-Results/'
AWS_REGION = 'us-east-1'
SAVED_QUERIES = {
    'loans_by_state' : """SELECT ProjectState, COUNT(*) AS total_loans, SUM(InitialApprovalAmount) AS total_approved, SUM(ForgivenessAmount) AS total_forgiven FROM paycheck_protection_program GROUP BY ProjectState ORDER BY total_approved DESC LIMIT 20""",

    'jobs_by_business_type': """ SELECT BusinessType, COUNT(*) AS total_loans, SUM(JobsReported) AS total_jobs, AVG(InitialApprovalAmount) AS avg_loan_amount FROM paycheck_protection_program GROUP BY BusinessType ORDER BY total_jobs DESC LIMIT 20""",

    'forgiveness_by_lender': """SELECT ServicingLenderName, COUNT(*) AS total_loans, SUM(InitialApprovalAmount) AS total_approved, SUM(ForgivenessAmount) AS total_forgiven, ROUND(SUM(ForgivenessAmount) / NULLIF(SUM(InitialApprovalAmount), 0) * 100, 2) AS forgiveness_rate_pct FROM paycheck_protection_program GROUP BY ServicingLenderName ORDER BY total_approved DESC LIMIT 20 """,
}

def frontend(request):
  
  return render(request, 'query.html', {
                'saved_queries' : SAVED_QUERIES,
                'saved_queries_json': json.dumps(SAVED_QUERIES),
                })
def athenaQuery(sql: str) -> dict:
  client = boto3.client('athena', region_name=AWS_REGION)

  response = client.start_query_execution(
    QueryString=sql,
    QueryExecutionContext={
      'Database': ATHENA_DATABASE,
      'Catalog': 'AwsDataCatalog'
    },
    ResultConfiguration={'OutputLocation' : ATHENA_OUTPUT}
  )
  query_id = response['QueryExecutionId']

  for _ in range(60):
    status = client.get_query_execution(QueryExecutionId = query_id)
    state = status['QueryExecution']['Status']['State']
    if state == 'SUCCEEDED':
      break
    elif state in ('FAILED', 'CANCELLED'): 
      reason = status['QueryExecution']['Status']['StateChangeReason']
      raise Exception(f"query {state} : {reason}")
    time.sleep(1)
  else:
    raise Exception("Query timed out after 60 seconds")
  
  results = client.get_query_results(QueryExecutionId = query_id)
  rows = results['ResultSet']['Rows']
  headers = [col['VarCharValue'] for col in rows[0]['Data']]
  data = [{headers[i]: col.get('VarCharValue', '') for i, col in enumerate(row['Data'])}
          for row in rows[1:]
        ]
  stats = status['QueryExecution']['Statistics']
  return{
    'headers':headers,
    'rows': data,
    'row_count': len(data),
    'scanned_mb': round(stats.get('DataScannedInBytes', 0) /1e6, 2),
    'duration_ms': stats.get('TotalExecutionTimeInMillis', 0 ) 
  }



def debug_settings(request):
    import os
    from django.http import JsonResponse
    return JsonResponse({
        'database': os.environ.get('ATHENA_DATABASE', 'ppp_data'),
        'output':   os.environ.get('ATHENA_OUTPUT', 's3://aws-s3-study-case/Paycheck-protection-program/Query-Results/'),
        'region':   os.environ.get('AWS_DEFAULT_REGION', 'us-east-1'),
    })

@csrf_exempt
@require_POST
def run_query(request):
  try:
    body = json.loads(request.body)
    query_key = body.get('query_key', '').strip()
    custom_sql = body.get('custom_sql', '').strip()

    if query_key and query_key in SAVED_QUERIES:
      sql = SAVED_QUERIES[query_key]
    elif custom_sql:
      sql = custom_sql
    else:
      return JsonResponse({'Error': 'No Query Provided.'}, status=400)
    
    result = athenaQuery(sql)
    return JsonResponse({'success': True, **result})
    

  except Exception as e:
    traceback.print_exc()
    return JsonResponse({'error': str(e)}, status=500)





