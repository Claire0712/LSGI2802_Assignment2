def active_interval(now,start,end):
 return start<=now<=end if start<=end else now>=start or now<=end
def allowed(kind,details,day='MON',now=1000):
 relevant=[r for r in details if r['DayCode'] in {day,'WD','ED'}]
 if kind not in ('OPEN','CLOSE'):return None
 if not details:return None
 inside=any(active_interval(now,int(r['FromTime']),int(r['ToTime'])) for r in relevant)
 return inside if kind=='OPEN' else not inside
