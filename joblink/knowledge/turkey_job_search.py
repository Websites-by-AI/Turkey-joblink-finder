"""Verified public search endpoints for Turkish jobs; no private data or auto-application."""
from urllib.parse import quote
SITES={
 'Kariyer.net':'https://www.kariyer.net/is-ilanlari/',
 'Indeed Türkiye':'https://tr.indeed.com/jobs?q=',
 'LinkedIn Jobs':'https://www.linkedin.com/jobs/search/?keywords=',
 'Yenibiriş':'https://www.yenibiris.com/is-ilanlari/',
 'Eleman.net':'https://www.eleman.net/is-ilanlari',
 'Secretcv':'https://www.secretcv.com/is-ilanlari',
 'Jooble Türkiye':'https://tr.jooble.org/i%C5%9F-ilanlar%C4%B1/',
 'Glassdoor':'https://www.glassdoor.com/Job/turkey-',
 'Talent.com':'https://tr.talent.com/jobs?k=',
 'İşin Olsun':'https://isinolsun.com/is-ilanlari',
}
CATEGORIES={
 'AI / Yapay Zeka':['Yapay Zeka Mühendisi','AI Engineer','Machine Learning Engineer','LLM Engineer','Computer Vision Engineer'],
 'Agentic AI / LLM':['AI Agent','Agentic AI','LLM Developer','RAG Engineer','Generative AI'],
 'Software Engineering':['Yazılım Mühendisi','Software Engineer','Backend Developer','Full Stack Developer','Python Developer'],
 'Maker / Robotics':['Robotik Mühendisi','Embedded Engineer','IoT Engineer','Mekatronik Mühendisi','Automation Engineer'],
 'Biomedical':['Biyomedikal Mühendisi','Biomedical Engineer','Medikal Cihaz','Clinical Engineer','Biyomedikal Teknikeri'],
 'Engineering':['Elektrik Elektronik Mühendisi','Makine Mühendisi','Endüstri Mühendisi','Veri Mühendisi','DevOps Engineer'],
}
def search_rows(category='AI / Yapay Zeka', site='All', limit=20):
    terms=CATEGORIES.get(category,CATEGORIES['AI / Yapay Zeka'])
    sites=SITES if site=='All' else {site:SITES.get(site,'')}
    rows=[]
    for term in terms:
        for name,base in sites.items():
            if len(rows)>=limit: return rows
            if 'indeed' in base or 'linkedin' in base or 'talent' in base:
                url=base+quote(term+' Turkey')
            else: url=base+quote(term.lower().replace(' ','+'))
            rows.append({'Kategori':category,'Arama':term,'Site':name,'Ülke':'Türkiye','Başvuru':url,'Not':'İlanın aktifliği ve çalışma izni başvuru sayfasında doğrulanmalı'})
    return rows

def all_rows(limit_each=20):
    return {cat:search_rows(cat,limit=limit_each) for cat in CATEGORIES}
