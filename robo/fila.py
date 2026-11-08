"""Fila de processos em SQLite: o robô pega os pendentes, e cada um termina CONCLUIDO, REVISAR (dado errado, não
adianta tentar de novo) ou ERRO (o portal falhou mais vezes que o limite)."""
import datetime as dt
import sqlite3

PENDENTE, CONCLUIDO, REVISAR, ERRO = "PENDENTE", "CONCLUIDO", "REVISAR", "ERRO"


def abrir(caminho):
    con = sqlite3.connect(caminho)
    con.row_factory = sqlite3.Row
    con.execute("""CREATE TABLE IF NOT EXISTS processos (
        id INTEGER PRIMARY KEY, nome TEXT NOT NULL, cpf TEXT NOT NULL, nascimento TEXT, renda REAL,
        modalidade TEXT, email TEXT, situacao TEXT NOT NULL DEFAULT 'PENDENTE', tentativas INTEGER NOT NULL DEFAULT 0,
        protocolo TEXT, motivo TEXT, atualizado_em TEXT)""")
    return con


def incluir(con, clientes):
    with con:
        con.executemany("INSERT INTO processos (nome, cpf, nascimento, renda, modalidade, email) "
                        "VALUES (:nome, :cpf, :nascimento, :renda, :modalidade, :email)", clientes)


def pendentes(con, limite=50):
    return [dict(r) for r in con.execute(
        "SELECT * FROM processos WHERE situacao = ? ORDER BY id LIMIT ?", (PENDENTE, limite))]


def _agora():
    return dt.datetime.now().isoformat(timespec="seconds")


def concluir(con, pid, protocolo):
    with con:
        con.execute("UPDATE processos SET situacao = ?, protocolo = ?, motivo = NULL, atualizado_em = ? WHERE id = ?",
                    (CONCLUIDO, protocolo, _agora(), pid))


def revisar(con, pid, motivo):
    with con:
        con.execute("UPDATE processos SET situacao = ?, motivo = ?, atualizado_em = ? WHERE id = ?",
                    (REVISAR, motivo, _agora(), pid))


def falhou(con, pid, motivo, limite=3):
    """Conta a tentativa; passou do limite, o processo vai para ERRO. Devolve True se ainda pode tentar."""
    with con:
        con.execute("UPDATE processos SET tentativas = tentativas + 1, motivo = ?, atualizado_em = ? WHERE id = ?",
                    (motivo, _agora(), pid))
        tentativas = con.execute("SELECT tentativas FROM processos WHERE id = ?", (pid,)).fetchone()[0]
        if tentativas >= limite:
            con.execute("UPDATE processos SET situacao = ? WHERE id = ?", (ERRO, pid))
            return False
    return True


def resumo(con):
    return dict(con.execute("SELECT situacao, COUNT(*) FROM processos GROUP BY situacao").fetchall())
