# De Mol Spel
Spelregels staan in "spel/". De app kan je ook gebruiken, doe
```bash
pip install -r requirements.txt
python app.py data/test1.csv data/extra.csv
```
test1.csv geeft de stemmen van mensen weer, extra.csv geeft de bonussen weer. Open dan een browser op http://127.0.0.1:5000, en vul de namen in van de spelers (Anon1, Anon2, ...). De drie spelers met de laagste score worden uitgeschakeld.