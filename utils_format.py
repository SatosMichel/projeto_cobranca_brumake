def formatar_cnpj(cnpj):
    cnpj = ''.join(filter(str.isdigit, str(cnpj)))
    if len(cnpj) != 14:
        return cnpj  # Retorna como está se não tiver 14 dígitos
    return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"

# Exemplo de uso:
# formatar_cnpj('12345678000199') -> '12.345.678/0001-99'

def formatar_data(data):
    """
    Converte uma data no formato 'YYYY-MM-DD' ou um objeto date/datetime
    para 'dd/MM/yyyy'. Se a entrada for vazia ou inválida, retorna a entrada original.
    """
    if not data:
        return ''
    # Se já for datetime/date
    try:
        from datetime import datetime, date
        if isinstance(data, (datetime, date)):
            return data.strftime('%d/%m/%Y')
    except Exception:
        pass
    # Se for string no formato ISO
    try:
        parts = str(data).split('-')
        if len(parts) == 3:
            yyyy, mm, dd = parts[0], parts[1], parts[2]
            # remover possível tempo em dd (ex: '2025-10-06T12:00:00')
            dd = dd.split('T')[0]
            return f"{dd.zfill(2)}/{mm.zfill(2)}/{yyyy}"
    except Exception:
        pass
    # fallback: retorna como veio
    return str(data)
