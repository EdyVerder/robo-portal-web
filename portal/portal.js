// Portal de mentira: login, formulário com validação e protocolo. De vez em quando fica "indisponível",
// como os portais de verdade, para o robô mostrar as novas tentativas.
const $ = (id) => document.getElementById(id);
const USUARIO = "demo.usuario", SENHA = "demo-2026";
const INSTAVEL = Number(new URLSearchParams(location.search).get("instavel") ?? "0.15");

function mostrar(tela) {
  for (const t of ["tela-login", "tela-cadastro", "tela-protocolo"]) $(t).hidden = t !== tela;
}

function esperar(ms) {
  $("carregando").hidden = false;
  return new Promise((ok) => setTimeout(() => { $("carregando").hidden = true; ok(); }, ms));
}

function erro(id, texto) {
  $(id).textContent = texto;
  $(id).hidden = !texto;
}

function cpfValido(cpf) {
  const d = cpf.replace(/\D/g, "");
  if (d.length !== 11 || /^(\d)\1+$/.test(d)) return false;
  const dv = (n) => {
    let s = 0;
    for (let i = 0; i < n; i++) s += Number(d[i]) * (n + 1 - i);
    const r = (s * 10) % 11;
    return r === 10 ? 0 : r;
  };
  return dv(9) === Number(d[9]) && dv(10) === Number(d[10]);
}

$("form-login").addEventListener("submit", async (e) => {
  e.preventDefault();
  erro("erro-login", "");
  await esperar(500);
  if ($("usuario").value === USUARIO && $("senha").value === SENHA) {
    sessionStorage.setItem("sessao", "1");
    mostrar("tela-cadastro");
  } else {
    erro("erro-login", "Usuário ou senha inválidos.");
  }
});

$("cpf").addEventListener("input", () => {
  const d = $("cpf").value.replace(/\D/g, "").slice(0, 11);
  $("cpf").value = d.replace(/(\d{3})(\d)/, "$1.$2").replace(/(\d{3})(\d)/, "$1.$2").replace(/(\d{3})(\d{1,2})$/, "$1-$2");
});

$("form-cadastro").addEventListener("submit", async (e) => {
  e.preventDefault();
  erro("erro-cadastro", "");
  const faltando = ["nome", "cpf", "nascimento", "renda", "modalidade", "email"].filter((c) => !$(c).value.trim());
  if (faltando.length) return erro("erro-cadastro", "Preencha todos os campos.");
  if (!cpfValido($("cpf").value)) return erro("erro-cadastro", "CPF inválido.");
  if (!$("aceite").checked) return erro("erro-cadastro", "Confirme a declaração antes de enviar.");
  await esperar(900);
  if (Math.random() < INSTAVEL) return erro("erro-cadastro", "Sistema temporariamente indisponível. Tente novamente.");
  const protocolo = "PC-" + new Date().getFullYear() + "-" + String(Math.floor(Math.random() * 1e6)).padStart(6, "0");
  $("protocolo").textContent = protocolo;
  $("form-cadastro").reset();
  mostrar("tela-protocolo");
});

$("novo").addEventListener("click", () => mostrar("tela-cadastro"));
$("sair").addEventListener("click", () => { sessionStorage.clear(); mostrar("tela-login"); });
if (sessionStorage.getItem("sessao")) mostrar("tela-cadastro");
