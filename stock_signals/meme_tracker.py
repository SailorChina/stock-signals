# -*- coding: utf-8 -*-
from __future__ import annotations
import os, json, logging
from dataclasses import dataclass
from datetime import date
from typing import Dict, List
logger = logging.getLogger('stock-signals')
_WATCHLIST_PATH = os.path.join(os.path.dirname(__file__), '.meme_watchlist.json')
@dataclass
class MemeStock:
    code: str; source: str; note: str; added_date: str; last_mentioned: str; mention_count: int
    def to_dict(self):
        return dict(code=self.code, source=self.source, note=self.note, added_date=self.added_date, last_mentioned=self.last_mentioned, mention_count=self.mention_count)
    @classmethod
    def from_dict(cls, d):
        return cls(d['code'], d.get('source','manual'), d.get('note',''), d.get('added_date',date.today().isoformat()), d.get('last_mentioned',date.today().isoformat()), d.get('mention_count',1))
def _load():
    if not os.path.exists(_WATCHLIST_PATH): return {}
    try:
        with open(_WATCHLIST_PATH,'r',encoding='utf-8') as f: return {c:MemeStock.from_dict(v) for c,v in json.load(f).items()}
    except Exception as e: logger.warning(f'  load meme WL failed: {e}'); return {}
def _save(wl):
    try:
        with open(_WATCHLIST_PATH,'w',encoding='utf-8') as f: json.dump({c:s.to_dict() for c,s in wl.items()}, f, ensure_ascii=False, indent=2)
    except Exception as e: logger.warning(f'  save meme WL failed: {e}')
def add_meme_stock(code, source='manual', note=''):
    if not code.startswith('US.'): return False
    wl=_load(); today=date.today().isoformat()
    if code in wl: wl[code].mention_count+=1; wl[code].last_mentioned=today
    else: wl[code]=MemeStock(code,source,note,today,today,1)
    _save(wl); logger.info(f'  Meme: added {code}')
    return True
def remove_meme_stock(code):
    wl=_load()
    if code in wl: del wl[code]; _save(wl); return True
    return False
def get_meme_stocks(): return sorted(_load().values(), key=lambda x:x.last_mentioned, reverse=True)
def get_meme_codes(): return [s.code for s in get_meme_stocks()]
def get_meme_bonus(code, default=1.0): return 1.05 if code in _load() else default
def list_meme_watchlist(): return [s.to_dict() for s in get_meme_stocks()]
def _can_reach_social():
    import urllib.request
    for url in ['https://x.com','https://www.youtube.com']:
        try:
            r=urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=3); return r.status==200
        except: pass
    return False
def scrape_maojie_x():
    if not _can_reach_social(): return []
    logger.warning('  scrape_maojie_x not yet implemented')
    return []
def scrape_maojie_youtube():
    if not _can_reach_social(): return []
    logger.warning('  scrape_maojie_youtube not yet implemented')
    return []
def auto_scrape():
    added=0
    try:
        for c in scrape_maojie_x():
            if add_meme_stock(c,source='maojie_x'): added+=1
    except Exception as e: logger.warning(f'  X scrape failed: {e}')
    try:
        for c in scrape_maojie_youtube():
            if add_meme_stock(c,source='maojie_yt'): added+=1
    except Exception as e: logger.warning(f'  YT scrape failed: {e}')
    return added
def init_default_watchlist():
    wl=_load()
    if wl: return
    defaults=[('US.NVDA','maojie_x','AI chip leader'),('US.TSLA','maojie_x','EV leader'),('US.MSFT','maojie_x','AI+Cloud'),('US.AAPL','maojie_x','Tech blue chip'),('US.META','maojie_x','AI+Social'),('US.AMZN','maojie_x','Ecommerce+AWS'),('US.AMD','maojie_x','Semiconductor'),('US.PLTR','maojie_x','AI Data'),('US.MSTR','maojie_x','Bitcoin+Software'),('US.COIN','maojie_x','Crypto exchange')]
    today=date.today().isoformat()
    for code,src,note in defaults: wl[code]=MemeStock(code,src,note,today,today,1)
    _save(wl); logger.info(f'  Meme: initialized {len(wl)} stocks')
