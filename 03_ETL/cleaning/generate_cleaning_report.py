"""Read-only TR-01..TR-15 audit and PDF report; run from repository root after M2.
No database credentials are written to disk. Uses standard PG* environment variables.
"""
import os, json, sys
from pathlib import Path
from datetime import datetime, timezone
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / '01_Project_Documentation' / 'phase2' / 'P2_02_Data_Cleaning_Report.pdf'
EVIDENCE = ROOT / '03_ETL' / 'run_reports' / 'khadija_m2_tr_evidence.json'

# Queries are read-only and use actual source/target objects.
# Metric descriptions are explicit: some count affected records, some count violations.
RULES = [
 ('TR-01','Business IDs / whitespace','M2 cleaning','Nonblank IDs, trimmed keys and deduplication',
  [('raw_blank_customer_ids',"SELECT count(*) FROM project_staging.stg_customers WHERE nullif(btrim(customer_id),'') IS NULL"),
   ('raw_customer_id_whitespace',"SELECT count(*) FROM project_staging.stg_customers WHERE customer_id <> btrim(customer_id)"),
   ('after_blank_customer_ids',"SELECT count(*) FROM project_staging.cln_customers WHERE nullif(btrim(customer_id),'') IS NULL"),
   ('after_duplicate_customer_ids',"SELECT count(*)-count(DISTINCT customer_id) FROM project_staging.cln_customers")]),
 ('TR-02','ZIP prefix as padded text','M2 cleaning','Preserve leading zeroes and five-character codes',
  [('raw_customer_zip_under_5',"SELECT count(*) FROM project_staging.stg_customers WHERE length(btrim(customer_zip_code_prefix))<5"),
   ('after_customer_zip_invalid',"SELECT count(*) FROM project_staging.cln_customers WHERE customer_zip_code_prefix IS NOT NULL AND customer_zip_code_prefix !~ '^[0-9]{5}$'"),
   ('after_customer_zip_leading_zero',"SELECT count(*) FROM project_staging.cln_customers WHERE customer_zip_code_prefix LIKE '0%'")]),
 ('TR-03','City name normalization','M2 cleaning','Trim, unaccent and title-case',
  [('raw_customer_city_needs_normalizing',"SELECT count(*) FROM project_staging.stg_customers WHERE customer_city IS DISTINCT FROM project_staging.m2_city(customer_city)"),
   ('after_customer_city_noncanonical',"SELECT count(*) FROM project_staging.cln_customers WHERE customer_city IS DISTINCT FROM project_staging.m2_city(customer_city)"),
   ('raw_seller_city_needs_normalizing',"SELECT count(*) FROM project_staging.stg_sellers WHERE seller_city IS DISTINCT FROM project_staging.m2_city(seller_city)"),
   ('after_seller_city_noncanonical',"SELECT count(*) FROM project_staging.cln_sellers WHERE seller_city IS DISTINCT FROM project_staging.m2_city(seller_city)")]),
 ('TR-04','Timestamp parsing and date keys','M2 cleaning + dimensions','Parse source timestamps; date dimension uses YYYYMMDD',
  [('raw_approval_missing',"SELECT count(*) FROM project_staging.stg_orders WHERE nullif(btrim(order_approved_at),'') IS NULL"),
   ('after_approval_null',"SELECT count(*) FROM project_staging.cln_orders WHERE approved_ts IS NULL"),
   ('raw_delivery_missing',"SELECT count(*) FROM project_staging.stg_orders WHERE nullif(btrim(order_delivered_customer_date),'') IS NULL"),
   ('after_delivery_null',"SELECT count(*) FROM project_staging.cln_orders WHERE delivered_ts IS NULL"),
   ('after_date_dimension_rows',"SELECT count(*) FROM project_dw.dim_date")]),
 ('TR-05','Customer identity mapping','M2 dimension; M3 fact lookup','Collapse order-specific IDs to unique customer identities',
  [('raw_customer_ids',"SELECT count(DISTINCT customer_id) FROM project_staging.stg_customers"),
   ('raw_unique_people',"SELECT count(DISTINCT customer_unique_id) FROM project_staging.stg_customers"),
   ('after_dim_customer_known',"SELECT count(*) FROM project_dw.dim_customer WHERE customer_key<>-1"),
   ('after_unknown_members',"SELECT count(*) FROM project_dw.dim_customer WHERE customer_key=-1")]),
 ('TR-06','Latest customer location (Type 1)','M2 dimension','Select most recent purchase location per unique customer',
  [('raw_people_multiple_zip',"SELECT count(*) FROM (SELECT customer_unique_id FROM project_staging.stg_customers GROUP BY customer_unique_id HAVING count(DISTINCT customer_zip_code_prefix)>1) q"),
   ('after_duplicate_customer_business_keys',"SELECT count(*)-count(DISTINCT customer_unique_id) FROM project_dw.dim_customer WHERE customer_key<>-1"),
   ('after_customer_dimension_known',"SELECT count(*) FROM project_dw.dim_customer WHERE customer_key<>-1")]),
 ('TR-07','Missing and untranslated product categories','M2 cleaning','Default missing categories; translate two exceptions',
  [('raw_missing_categories',"SELECT count(*) FROM project_staging.stg_products WHERE nullif(btrim(product_category_name),'') IS NULL"),
   ('after_uncategorized',"SELECT count(*) FROM project_staging.cln_products WHERE category_en='uncategorized'"),
   ('after_null_category_en',"SELECT count(*) FROM project_staging.cln_products WHERE category_en IS NULL"),
   ('after_manual_translations',"SELECT count(*) FROM project_staging.cln_products WHERE category_pt IN ('pc_gamer','portateis_cozinha_e_preparadores_de_alimentos')")]),
 ('TR-08','Correct product column spelling','M2 cleaning','Rename *_lenght source fields to *_length target fields',
  [('raw_typo_columns',"SELECT count(*) FROM information_schema.columns WHERE table_schema='project_staging' AND table_name='stg_products' AND column_name IN ('product_name_lenght','product_description_lenght')"),
   ('after_corrected_columns',"SELECT count(*) FROM information_schema.columns WHERE table_schema='project_staging' AND table_name='cln_products' AND column_name IN ('name_length','description_length')"),
   ('after_product_rows',"SELECT count(*) FROM project_staging.cln_products")]),
 ('TR-09','Geolocation range filter and median','M2 cleaning','Exclude out-of-range points, group by ZIP and calculate medians',
  [('raw_geolocation_rows',"SELECT count(*) FROM project_staging.stg_geolocation"),
   ('raw_outside_range',"SELECT count(*) FROM project_staging.stg_geolocation WHERE project_staging.m2_num(geolocation_lat) NOT BETWEEN -34 AND 6 OR project_staging.m2_num(geolocation_lng) NOT BETWEEN -74 AND -34"),
   ('raw_duplicate_full_rows',"SELECT count(*)-count(DISTINCT ROW(geolocation_zip_code_prefix,geolocation_lat,geolocation_lng,geolocation_city,geolocation_state)) FROM project_staging.stg_geolocation"),
   ('after_zip_medians',"SELECT count(*) FROM project_staging.cln_zip_geo"),
   ('after_outside_range',"SELECT count(*) FROM project_staging.cln_zip_geo WHERE latitude NOT BETWEEN -34 AND 6 OR longitude NOT BETWEEN -74 AND -34")]),
 ('TR-10','Unknown dimension members','M2 dimensions; M3 lookup','One -1 record per dimension; downstream FK fallback belongs to M3',
  [('after_unknown_members_total',"SELECT (SELECT count(*) FROM project_dw.dim_customer WHERE customer_key=-1)+(SELECT count(*) FROM project_dw.dim_product WHERE product_key=-1)+(SELECT count(*) FROM project_dw.dim_seller WHERE seller_key=-1)+(SELECT count(*) FROM project_dw.dim_date WHERE date_key=-1)+(SELECT count(*) FROM project_dw.dim_payment_type WHERE payment_type_key=-1)+(SELECT count(*) FROM project_dw.dim_order_status WHERE order_status_key=-1)"),
   ('after_null_customer_keys',"SELECT count(*) FROM project_dw.dim_customer WHERE customer_key IS NULL")]),
 ('TR-11','Zero payment installments','M2 cleaning','Replace zero installments with one',
  [('raw_zero_installments',"SELECT count(*) FROM project_staging.stg_order_payments WHERE project_staging.m2_num(payment_installments)=0"),
   ('after_zero_installments',"SELECT count(*) FROM project_staging.cln_payments WHERE payment_installments=0"),
   ('after_one_installment',"SELECT count(*) FROM project_staging.cln_payments WHERE payment_installments=1")]),
 ('TR-12','Delivery lags and late-delivery measures','M3 facts — not M2','M2 preserves timestamps; computed fact measures require M3',
  [('after_orders_with_delivery_timestamp',"SELECT count(*) FROM project_staging.cln_orders WHERE delivered_ts IS NOT NULL"),
   ('after_orders_missing_delivery_timestamp',"SELECT count(*) FROM project_staging.cln_orders WHERE delivered_ts IS NULL")]),
 ('TR-13','Out-of-sequence timestamps','M2 preserves; M3 flags','Do not delete anomalous orders; flagging/negative lag exclusion belongs to M3',
  [('raw_carrier_before_approval',"SELECT count(*) FROM project_staging.stg_orders WHERE project_staging.m2_ts(order_delivered_carrier_date)<project_staging.m2_ts(order_approved_at)"),
   ('after_carrier_before_approval',"SELECT count(*) FROM project_staging.cln_orders WHERE carrier_ts<approved_ts"),
   ('raw_delivery_before_carrier',"SELECT count(*) FROM project_staging.stg_orders WHERE project_staging.m2_ts(order_delivered_customer_date)<project_staging.m2_ts(order_delivered_carrier_date)"),
   ('after_delivery_before_carrier',"SELECT count(*) FROM project_staging.cln_orders WHERE delivered_ts<carrier_ts")]),
 ('TR-14','Per-order aggregates before joins','M3 facts — not M2','M2 supplies typed item/payment/review rows for downstream grouping',
  [('after_clean_order_items',"SELECT count(*) FROM project_staging.cln_order_items"),
   ('after_clean_payments',"SELECT count(*) FROM project_staging.cln_payments"),
   ('after_clean_reviews',"SELECT count(*) FROM project_staging.cln_reviews")]),
 ('TR-15','UTF-8-SIG category file ingestion','M1 source loading — not M2','M1 loader handles encoding; M2 joins translated categories',
  [('raw_translation_rows',"SELECT count(*) FROM project_staging.stg_category_translation"),
   ('after_translated_products',"SELECT count(*) FROM project_staging.cln_products WHERE category_en IS NOT NULL AND category_en<>'uncategorized'")]),
]

COUNTS = [('stg_customers','cln_customers'),('stg_orders','cln_orders'),('stg_order_items','cln_order_items'),('stg_order_payments','cln_payments'),('stg_order_reviews','cln_reviews'),('stg_products','cln_products'),('stg_sellers','cln_sellers'),('stg_geolocation','cln_zip_geo')]

def collect():
    import psycopg
    connkw = {k[2:].lower(): os.environ[k] for k in ('PGHOST','PGPORT','PGUSER') if k in os.environ}
    connkw['dbname']=os.environ.get('OLIST_DB','olist_commerce360')
    # libpq automatically reads PGPASSWORD or pgpass, never persist credentials
    data={'generated_utc':datetime.now(timezone.utc).isoformat(),'source':'live PostgreSQL','rules':[], 'table_counts':[]}
    with psycopg.connect(**connkw) as conn:
        with conn.cursor() as cur:
            for raw,clean in COUNTS:
                cur.execute('SELECT count(*) FROM project_staging.'+raw); before=cur.fetchone()[0]
                cur.execute('SELECT count(*) FROM project_staging.'+clean); after=cur.fetchone()[0]
                data['table_counts'].append({'source':raw,'target':clean,'before':before,'after':after,'delta':after-before})
            for rid,title,owner,explain,queries in RULES:
                item={'id':rid,'title':title,'owner':owner,'explanation':explain,'metrics':{}}
                for key,query in queries:
                    cur.execute(query)
                    item['metrics'][key]=cur.fetchone()[0]
                data['rules'].append(item)
    return data

def render(data):
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, KeepTogether
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='RuleTitleCustom',parent=styles['Heading2'],fontSize=11,spaceBefore=14,spaceAfter=6,textColor=colors.HexColor('#17365D')))
    styles.add(ParagraphStyle(name='SmallCustom',parent=styles['Normal'],fontSize=8.3,leading=12,spaceAfter=5))
    doc=SimpleDocTemplate(str(OUT),pagesize=A4,rightMargin=42,leftMargin=42,topMargin=42,bottomMargin=44)
    story=[Paragraph('Olist Commerce360 | Phase 2',styles['Title']),Paragraph('M2 Data Cleaning and Transformation Evidence Report',styles['Heading1']),Paragraph('Owner: Khadija Faiz (M2) | PostgreSQL | '+escape(data['generated_utc']),styles['SmallCustom'])]
    story.append(Paragraph('<b>Evidence classification:</b> '+('Live query results from the running project database.' if data['source']=='live PostgreSQL' else 'Known execution counts from the 2026-11-18 Colab session; per-rule metrics marked NOT YET MEASURED until the generator is run on the live database.'),styles['SmallCustom']))
    story.append(Paragraph('Scope and method',styles['Heading2']))
    story.append(Paragraph('Raw Olist CSVs are loaded into nine project_staging.stg_* tables by M1. M2 transforms them into eight project_staging.cln_* tables and loads six project_dw.dim_* tables. This report compares source and target row counts and evaluates TR-01 through TR-15 with rule-specific read-only queries. Counts represent different grains where noted; a row-count decrease is not automatically a deleted business record.',styles['SmallCustom']))
    story.append(Paragraph('Source-to-cleaned table row counts',styles['Heading2']))
    rows=[['Source','Cleaned target','Before','After','Change']]
    for x in data['table_counts']:
        fmt=lambda v: format(v,',') if isinstance(v,int) else str(v)
        rows.append([x['source'],x['target'],fmt(x['before']),fmt(x['after']),fmt(x['delta'])])
    t=Table(rows,colWidths=[110,110,75,75,75],repeatRows=1,hAlign='LEFT');t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#17365D')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('FONTSIZE',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.whitesmoke,colors.white]),('GRID',(0,0),(-1,-1),0.3,colors.lightgrey)]));story.append(t)
    story.append(Spacer(1,12))
    story.append(Paragraph('Important interpretation: geolocation changes grain from one source coordinate record to one ZIP-prefix median. Customer dimension changes grain from order-specific customer_id to customer_unique_id. Other count changes may arise from key validation and deduplication.',styles['SmallCustom']))
    story.append(Paragraph('Transformation-rule audit (TR-01 to TR-15)',styles['Heading2']))
    for r in data['rules']:
        block=[Paragraph(r['id']+' | '+escape(r['title']),styles['RuleTitleCustom']),Paragraph('<b>Responsibility:</b> '+escape(r['owner'])+'. <b>Implementation:</b> '+escape(r['explanation']),styles['SmallCustom'])]
        metricrows=[['Before / source evidence','Count','After / target evidence','Count']]
        before=[(k,v) for k,v in r['metrics'].items() if k.startswith('raw_')]
        after=[(k,v) for k,v in r['metrics'].items() if k.startswith('after_')]
        for i in range(max(len(before),len(after),1)):
            b=before[i] if i<len(before) else ('','')
            a=after[i] if i<len(after) else ('','')
            metricrows.append([Paragraph(escape(b[0].replace('_',' ')),styles['SmallCustom']),str(b[1]),Paragraph(escape(a[0].replace('_',' ')),styles['SmallCustom']),str(a[1])])
        mt=Table(metricrows,colWidths=[172,50,172,50],repeatRows=1,hAlign='LEFT');mt.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#E6EEF6')),('FONTSIZE',(0,0),(-1,-1),7.5),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,-1),0.3,colors.lightgrey),('BOTTOMPADDING',(0,0),(-1,-1),4)]))
        block.append(mt)
        if r['id'] in ('TR-12','TR-14','TR-15'):
            block.append(Paragraph('<i>Ownership boundary: the metric shown is M2 input or downstream context, not proof that the assigned M1/M3 transformation ran.</i>',styles['SmallCustom']))
        story.append(KeepTogether(block))
    story.append(Paragraph('Execution evidence and limitations',styles['Heading2']))
    story.append(Paragraph('Recorded 2026-11-18 session: 10/10 selected M1+M2 pipeline stages successful; 8/8 cleaned tables and 6/6 dimensions populated; 47/47 M2 structural and rerun checks passed; zero NULL or duplicate dimension surrogate keys; one unknown (-1) member per dimension; row counts stable after rerun. These results are independently supplied by the project operator and should not be confused with rule-specific metrics unless live queries have been executed.',styles['SmallCustom']))
    story.append(Paragraph('TR-12 and TR-14 are downstream M3 fact-stage requirements; TR-15 is handled by M1 ingestion. TR-13 requires M3 to flag anomalies, while M2 preserves those records. TR-16 (in the data dictionary but outside the requested TR-01 to TR-15 scope) requires fact revenue reconciliation and is not claimed here.',styles['SmallCustom']))
    story.append(Paragraph('Reproducibility: run python 03_ETL/cleaning/generate_cleaning_report.py from the repository root after the 10 M1+M2 stages. The script reads standard PG* environment variables, issues only SELECT queries, writes the JSON evidence file, and regenerates this PDF. Re-run after source data or cleaning logic changes.',styles['SmallCustom']))
    def footer(canvas,doc):
        canvas.setFont('Helvetica',8);canvas.setFillColor(colors.grey);canvas.drawString(42,27,'Olist Commerce360 | M2 | Phase 2');canvas.drawRightString(A4[0]-42,27,'Page '+str(doc.page))
    doc.build(story,onFirstPage=footer,onLaterPages=footer)

if __name__=='__main__':
    try:
        data=collect()
    except Exception as e:
        print('Live database query failed: '+str(e),file=sys.stderr)
        print('No report was generated. Verify PG* settings, database and completed M2 stages.',file=sys.stderr)
        sys.exit(1)
    EVIDENCE.parent.mkdir(parents=True,exist_ok=True)
    EVIDENCE.write_text(json.dumps(data,indent=2,default=str),encoding='utf-8')
    render(data)
    print('Generated:',OUT,'\nEvidence:',EVIDENCE)
