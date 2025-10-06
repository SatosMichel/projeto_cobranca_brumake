def valor_por_extenso(valor):
    """Converte valor numérico (float ou int) para extenso em português (reais e centavos).
    Exemplo: 5500.00 -> 'Cinco mil e quinhentos reais'
    Esta implementação cobre valores positivos razoáveis até milhões.
    """
    unidades = ['zero','um','dois','três','quatro','cinco','seis','sete','oito','nove','dez','onze','doze','treze','quatorze','quinze','dezesseis','dezessete','dezoito','dezenove']
    dezenas = ['','','vinte','trinta','quarenta','cinquenta','sessenta','setenta','oitenta','noventa']
    centenas = ['','cento','duzentos','trezentos','quatrocentos','quinhentos','seiscentos','setecentos','oitocentos','novecentos']

    def inteiro_para_extenso(n):
        if n < 20:
            return unidades[n]
        if n < 100:
            d = n // 10
            r = n % 10
            if r == 0:
                return dezenas[d]
            return dezenas[d] + ' e ' + unidades[r]
        if n == 100:
            return 'cem'
        if n < 1000:
            c = n // 100
            r = n % 100
            if r == 0:
                return centenas[c]
            return centenas[c] + ' e ' + inteiro_para_extenso(r)
        if n < 1000000:
            m = n // 1000
            r = n % 1000
            parte_m = ''
            if m == 1:
                parte_m = 'mil'
            else:
                parte_m = inteiro_para_extenso(m) + ' mil'
            if r == 0:
                return parte_m
            return parte_m + ' ' + inteiro_para_extenso(r)
        # para valores maiores, usar notação com milhões
        if n < 1000000000:
            mm = n // 1000000
            r = n % 1000000
            parte_mm = inteiro_para_extenso(mm) + ' milhão' + ('s' if mm > 1 else '')
            if r == 0:
                return parte_mm
            return parte_mm + ' ' + inteiro_para_extenso(r)
        return str(n)

    # Normalizar
    try:
        total = float(valor)
    except Exception:
        return ''
    if total < 0:
        return 'menos ' + valor_por_extenso(abs(total))
    reais = int(total)
    centavos = int(round((total - reais) * 100))

    partes = []
    if reais == 0:
        partes.append('zero reais')
    else:
        texto_reais = inteiro_para_extenso(reais)
        texto_reais = texto_reais.capitalize()
        partes.append(texto_reais + (' real' if reais == 1 else ' reais'))
    if centavos:
        texto_cent = inteiro_para_extenso(centavos)
        partes.append('e ' + texto_cent + (' centavo' if centavos == 1 else ' centavos'))
    return ' '.join(partes)


def numero_por_extenso(n):
    """Retorna o número inteiro n por extenso (minúsculo), sem sufixos de moeda.
    Ex: 2 -> 'dois'
    """
    try:
        n_int = int(round(float(n)))
    except Exception:
        return ''

    unidades = ['zero','um','dois','três','quatro','cinco','seis','sete','oito','nove','dez','onze','doze','treze','quatorze','quinze','dezesseis','dezessete','dezoito','dezenove']
    dezenas = ['','','vinte','trinta','quarenta','cinquenta','sessenta','setenta','oitenta','noventa']
    centenas = ['','cento','duzentos','trezentos','quatrocentos','quinhentos','seiscentos','setecentos','oitocentos','novecentos']

    def inteiro_para_extenso(n):
        if n < 20:
            return unidades[n]
        if n < 100:
            d = n // 10
            r = n % 10
            if r == 0:
                return dezenas[d]
            return dezenas[d] + ' e ' + unidades[r]
        if n == 100:
            return 'cem'
        if n < 1000:
            c = n // 100
            r = n % 100
            if r == 0:
                return centenas[c]
            return centenas[c] + ' e ' + inteiro_para_extenso(r)
        if n < 1000000:
            m = n // 1000
            r = n % 1000
            parte_m = ''
            if m == 1:
                parte_m = 'mil'
            else:
                parte_m = inteiro_para_extenso(m) + ' mil'
            if r == 0:
                return parte_m
            return parte_m + ' ' + inteiro_para_extenso(r)
        if n < 1000000000:
            mm = n // 1000000
            r = n % 1000000
            parte_mm = inteiro_para_extenso(mm) + ' milhão' + ('s' if mm > 1 else '')
            if r == 0:
                return parte_mm
            return parte_mm + ' ' + inteiro_para_extenso(r)
        return str(n_int)

    return inteiro_para_extenso(n_int)


def percentual_por_extenso(value):
    """Retorna a representação em palavras de um percentual.
    Exemplos: 2 -> 'dois por cento', 2.5 -> 'dois vírgula cinco por cento'
    """
    try:
        v = float(value)
    except Exception:
        return ''
    # separar parte inteira e decimal
    inteiro = int(v)
    frac = v - inteiro
    if abs(frac) < 1e-9:
        # inteiro
        return f"{numero_por_extenso(inteiro)} por cento"
    # tem parte decimal
    # pegar representação decimal sem zeros finais
    s = ('%.10f' % v).rstrip('0').rstrip('.')
    if '.' in s:
        parts = s.split('.')
        int_part = int(parts[0])
        frac_part = parts[1]
        # representar a parte decimal: se um dígito, converter para palavra; se mais, converter como número
        if len(frac_part) == 1:
            unidades_map = {
                '0':'zero','1':'um','2':'dois','3':'três','4':'quatro','5':'cinco','6':'seis','7':'sete','8':'oito','9':'nove'
            }
            frac_text = unidades_map.get(frac_part, frac_part)
        else:
            try:
                frac_num = int(frac_part)
                frac_text = numero_por_extenso(frac_num)
            except Exception:
                frac_text = frac_part
        return f"{numero_por_extenso(int_part)} vírgula {frac_text} por cento"
    else:
        return f"{numero_por_extenso(inteiro)} por cento"
