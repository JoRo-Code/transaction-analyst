Sortera på qliro och vald period i export ordersfil (WGR)

Filtrera enligt nedan på betald vs ej betald och att belopp stämmer

Summera i total in på månad utifrån moms ej moms enl nedan

mombelopp från qliro == FEL!!!

Transaktionsslutdatum

avräkning = nr de betalar ut - ska kollas och är vad som avgör om de hamnar i summation 1 eller 2

De som inte finns hamnar i rad längst ned

SUMMADATA kan presenteras högst i filen



INPUT

FILE 1 - 3mån

FILE 2

INTERVALL FÖR peiord


OUTPUT

INK TOTAL KR 100

EX MOMS

25% 20

6%

ORDRAR ORDERNR och belopp SOM EJ UTBETALDA MÅNADENS SLUT MEN BETLD SENARE

TABELL INK TOTAL EX 25% 6%
54445 

ORDRAR  SOM EJ BETALTS!!!


____

QLIROCHECKOUT

Butiksordernummer - ORDER ID

avräkningsdatum utanför tidsperioden:
    settled v 

betalda:
    - sorteras på momsbelopp
        hur många som är ex moms %

        total för period: exmoms konto, 25% 6% 
betalda ej inom perioden/efter perioden
ej betalda:
    skriva ut ordrar (error elr liknande)

ej wgr men qliro:
    drop


avräkningsdatum utanför perioden sätt på nästa period

Få en summerad fil