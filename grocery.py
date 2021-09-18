# coding: utf-8
import glob
import pdftotext
import re
import pandas as pd
import logging

"""
        "": [],
        "": [],
        "": [],
        "": [],
        "": [],
        "": [],
        "": [],
"""

category_dict = {
        "drogerie": [ "lapač", "zubní", "kartáček", "myčk", "plenky", "Sáčky", "Alobal", "Frosch", "Toaletní", ],
        "hračky": [ "Models", "small foot", ],
        "ovoce": [ "Citron", "jablk", "Mandarinka", "zelenin", "Jablk", "borůvky", "banán", "Meloun", "Hrozny", "Mango", "Pomeranč", "Hruška", "Blum", "Pomelo", "Jahody", "Švestka", "Lesní směs", "Kiwi",  ],
        "zelenina": [ "Ředkvičky", "rajč", "Rajč", "Fresh bedýnky", "batát", "brambor", "Pór", "Okurk", "Květák", "Lilek", "Ajvar", "Avokádo", "olivy", "Hrach", "Mrkev", "Zázvor", "Česnek", "Paprik", "Cuketa", "Kedlubna", "Řepa", "Cibule", "Špenát", "Hrášek", "Brokolice", "Celer", "kukuřice", "Tikka kari", "cherry", "Petržel", "Kopr", "hadovka", "Tulipán", ],
        "mléčné výrobky": [ "mlék", "Mlék", "mléč", "Bryndza", "Mléč", "Smetana", "jogurt", "Tvaroh", "Jogurt", "Eidam", "Cheddar", "Mozzarella", "Lipánek", "Gouda", "Pribináček", "sýr", "máslo", "Müller", "Ehrmann", "Hermelín", "Gervais", ],
        "maso": [ "Hovězí", "maso", "Maso", "Slanina", "Šunka", "Buřt", "párek", "klobása", "Kuřecí prsa", "řízky", ],
        "přílohy": [ "Fazole", "Rýže", "knedlík", "Penne", "krokety", "Čočka", "hořčice", "těstoviny", "vločky", "kaše", ],
        "musli": [ "müsli", "mysli", "Müsli", "Musli", "Mysli"],
        "vegan": [ "Vegup", "Sojov", "soj", "sój", "Tapioka", "Sproud", "Tofu", "Sushi", "Šmakoun", ],
        "sladkosti": [ "JOJO", "piškot", "Nutrend", "Algida", "Ovocňák", "Haribo", "Míša", "Kinder Pingui", "Nutella", "Pedro", "Cornies", "Gelfix", "Cukr", "sůl", "sušenky", "křupky", "Bohemia", "tyčinky", "Mozartkugeln", "Mrož", ],
        "pečivo": [ "Pletenec", "těsto", "Vánočka", "vánočka", "houska", "chléb", "Placka", "tyčky", "chleb", "tortill", "droždí", "Preclík", "Čokorolka", "Rohlík", "Mouka", ],
        "nápoje":  [ "pivo", "džus", "Birell", "Coca", "Cool", "čaj", "víno", "Merlot", "Top Topic", ],
        "zvíře": [ "kočk", "Cat chunks", "Whiskas", "psy", "Kost žvýkací", ],
        "vratné": [ "vratné obaly", ],
        }

getDatum    = re.compile("\d\d\.\d\d\.\d\d\d\d")
getHeader   = re.compile("^.*Doručené položky", re.MULTILINE)
getHeader2  = re.compile("^.*Velká Pecka s.r.o.", re.MULTILINE)
getFooter   = re.compile("Doprava a platba.*$", re.MULTILINE)
getPrice    = re.compile("-?\d+,\d+ Kč$", re.MULTILINE)
getAmount   = re.compile("([\.\d]+) ?(kg)? ?× ([\d,]+) (Kč)?")
splitPrice  = re.compile(" Kč$", re.MULTILINE)
def parse_pdf( text ):
    datum = getDatum.search(text)
    datum = datum.group()
    header_body_split = getHeader.split(text)
    if (len(header_body_split) == 2):
        header, body = header_body_split
    else:
        header, body, _, __ = getHeader2.split(text)
    body, footer = getFooter.split(body)
    
    item_names, dates, prices, amounts, units, unit_prices, categories = [], [], [], [], [], [], []
    start_index, items = 0, []
    for find in getPrice.finditer(body):
        items.append(body[start_index : find.end()].strip())
        start_index = find.end()
    for item in items:
        price = getPrice.search(item)
        if "-" in price.group(): #negative price
            pass
        else:
            try:
                item_name, amount, unit, unit_price = parse_item(item)
                item_names.append(item_name)
                prices.append(price.group())
                amounts.append(amount)
                units.append(unit)
                unit_prices.append(unit_price)
                dates.append(datum)
                categories.append(get_category(item_name))
            except:
                logging.warning(f"item parsing error: {item}")
    return pd.DataFrame({ "name": item_names, "amount": amounts, "unit_price": unit_prices, "units": units, "price": prices, "date": dates, "category": categories})

def parse_item( item ):
    item_name = item.splitlines()[0]
    amount_search = getAmount.search(item.replace("\n", ""))
    if amount_search:
        amount, unit, unit_price, _ = amount_search.groups()
    else:
        logging.warning(f"amount search error {item}")
        amount, unit, unit_price = None, None, None
    return item_name, amount, unit, unit_price

def get_category( item_name ):
    category = None
    for key, patterns in category_dict.items():
        for pattern in patterns:
            #print("***", item_name, pattern, pattern in item_name)
            searchPattern = re.compile(pattern, re.IGNORECASE)
            if searchPattern.search(item_name):
                category = key
    if (not category):
        logging.warning(f"no category found for {item_name}")
    return category

dfs = []
files = glob.glob("*.pdf")
for fi in files:
    print(fi)
    with open(fi, "rb") as f:
        pdf = pdftotext.PDF(f)
        text = [] 
        for page in pdf:
            text.append(page)
        df = parse_pdf( "".join(text) )
        dfs.append(df)
df = pd.concat(dfs)
#print(df.head())
df.to_csv("grocery.csv")
nocat = df.loc[ pd.isna( df['category'] ) ]
print(nocat)
