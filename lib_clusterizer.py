# coding: utf-8

import datetime

class clusterizer:
    
    def __init__( self,
                  db=None,
                  start_date = datetime.date.today(),
                  end_date = datetime.datetime.today(),
                  field = 'doc_title',
                  threshold = 0.7
                  ):
        self.db = db
        self.start_date = start_date 
        self.end_date = end_date
        self.field = field
        self.threshold = threshold
        self.found = []
        
    def run(self):
        started_time = datetime.datetime.now()
        self.found = []
        if self.db:
            cur = self.db.cursor()
            sql = "select id, doc_date, "+self.field + ", doc_link, string_to_array(cast(plainto_tsquery(" \
                + self.field + ") as text), ' & '), source_id " \
                + "from docs where doc_date >= %s and doc_date <= %s " \
                + "order by doc_date, id"
            params = (self.start_date, self.end_date)
            cur.execute(sql, params)
            res = cur.fetchall()
            cur.close()
            self.db.commit()
            #
        for i in range(len(res)-1):
            cluster = []
            ids = []
            cluster.append( {'id':res[i][0], 'date':res[i][1], self.field:res[i][2], 'link':res[i][3]} )
            ids.append(res[i][0])
            for j in range(i+1, len(res)):
                if res[i][5] <> res[j][5]:
                    count = 0
                    coeff = 0
                    for k in res[i][4]:
                        if k in res[j][4]:
                            count +=1
                    total_len = len(res[i][4]) + len(res[j][4])
                    if total_len == 0:
                        coeff = 0
                    else:
                        coeff = 2.0*count / total_len
                    if coeff >= self.threshold:
                        cluster.append( {'id':res[j][0], 'date':res[j][1], self.field:res[j][2], 'link':res[j][3]} )
                        ids.append( res[j][0] )
        
            if len(cluster) > 1:
                found_cluster = []
                for n in ids:
                    for k in self.found:
                        if n in k['ids']:
                            found_cluster = k
                            break
                if found_cluster:
                    found_cluster['cluster'].extend( [c for c in cluster if c['id'] not in found_cluster['ids']])
                    found_cluster['ids'].extend( [c for c in ids if c not in found_cluster['ids']])
                else:
                    self.found.append( {'id':cluster[0]['id'],
                                        'date':cluster[0]['date'],
                                        self.field:cluster[0][self.field],
                                        'link':cluster[0]['link'],
                                        'cluster':cluster[:],
                                        'ids': ids[:] })
        #print datetime.datetime.now()-started_time
        return self
    
    def run_trgm(self):
        started_time = datetime.datetime.now()
        self.found = []
        if self.db:
            cur = self.db.cursor()
            sql = "select d1.id, d1.doc_date, d1."+self.field + ", d1.doc_link, " \
                + "d1."+self.field+" <-> d2."+self.field+", " \
                + "d2.id, d2.doc_date, d2."+self.field + ", d2.doc_link " \
                + "from docs d1, docs d2 " \
                + "where d1.id <> d2.id and d1.source_id <> d2.source_id " \
                + "and d1.doc_date >= %s and d1.doc_date <= %s and d2.doc_date >= %s and d2.doc_date <= %s " \
                + "and d1."+self.field + " <-> d2."+self.field+" <= " + str(1-self.threshold) + " " \
                + "order by d1.doc_date, d1.id"
            params = (self.start_date, self.end_date, self.start_date, self.end_date)
            cur.execute(sql, params)
            res = cur.fetchall()
            cur.close()
            self.db.commit()
            #
            for i in res:
                found_left = False
                found_right = False
                found_k = []
                for k in self.found:
                    if i[0] in k['ids']:
                        found_left = True
                    if i[5] in k['ids']:
                        found_right = True
                    if found_left or found_right:
                        found_k = k
                        break
                if found_left and not found_right:
                    found_k['cluster'].append({'id':i[5], 'date':i[6], self.field:i[7], 'link':i[8]})
                    found_k['ids'].append(i[5])
                if found_right and not found_left:
                    found_k['cluster'].append({'id':i[0], 'date':i[1], self.field:i[2], 'link':i[3]})
                    found_k['ids'].append(i[0])
                if (not found_left) and (not found_right): 
                    cluster = []
                    cluster.append( {'id':i[0], 'date':i[1], self.field:i[2], 'link':i[3]} )
                    cluster.append( {'id':i[5], 'date':i[6], self.field:i[7], 'link':i[8]} )
                    self.found.append( {'id':cluster[0]['id'],
                                        'date':cluster[0]['date'],
                                        self.field:cluster[0][self.field],
                                        'link':cluster[0]['link'],
                                        'cluster':cluster[:],
                                        'ids': [i[0], i[5]] })
        print datetime.datetime.now()-started_time
        return self
#------------------------------------------------------------------
