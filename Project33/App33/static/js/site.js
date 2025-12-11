class Base64 {
    static #textEncoder = new TextEncoder();
    static #textDecoder = new TextDecoder();

    // https://datatracker.ietf.org/doc/html/rfc4648#section-4
    static encode = (str) => btoa(String.fromCharCode(...Base64.#textEncoder.encode(str)));
    static decode = (str) => Base64.#textDecoder.decode(Uint8Array.from(atob(str), c => c.charCodeAt(0)));
    
    // https://datatracker.ietf.org/doc/html/rfc4648#section-5
    static encodeUrl = (str) => this.encode(str).replace(/\+/g, '-').replace(/\//g, '_'); //.replace(/=+$/, '');
    static decodeUrl = (str) => this.decode(str.replace(/\-/g, '+').replace(/\_/g, '/'));

    static jwtEncodeBody = (header, payload) => this.encodeUrl(JSON.stringify(header)) + '.' + this.encodeUrl(JSON.stringify(payload));
    static jwtDecodePayload = (jwt) => JSON.parse(this.decodeUrl(jwt.split('.')[1]));
}

document.addEventListener('DOMContentLoaded', () => {
    console.log("Script works");
    let btn = document.getElementById('btn-seed');
    if (btn) {
        btn.addEventListener('click', btnSeedClick);
    }
    btn = document.getElementById('auth-modal-btn');
    if (btn) {
        btn.addEventListener('click', btnAuthModalClick);
    }
    btn = document.getElementById('btn-auth-test');
    if (btn) {
        btn.addEventListener('click', btnAuthTestClick);
    }
    btn = document.getElementById('btn-auth-test-no-header');
    if (btn) {
        btn.addEventListener('click', btnAuthTestNoHeaderClick);
    }
    btn = document.getElementById('btn-auth-test-invalid-scheme');
    if (btn) {
        btn.addEventListener('click', btnAuthTestInvalidSchemeClick);
    }
});

function btnAuthTestInvalidSchemeClick() {
    fetch("/test/", {
        headers: {
            "Authorization": "Basic invalidscheme"
        }
    }).then(r => r.text()).then(alert);
}

function btnAuthTestNoHeaderClick() {
    fetch("/test/",{method:"GET"}).then(r=>r.text()).then(alert)
}

function btnAuthTestClick() {
    
    if(typeof window.auth_token=="undefined"){
        alert("Необхідно автентифікуватися")
    }else{
        console.log("Я працюю");
            fetch("/test/",
            {
                headers:{
                    "Authorization": "Bearer " + window.auth_token
                }
            }
        ).then(r=>{
            r.text().then(alert)
        })
    }
}
function btnAuthModalClick() {
    const loginInput = document.getElementById('auth-modal-login');
    if(!loginInput) throw "auth-modal-login element not found";
    const passwordInput = document.getElementById('auth-modal-password');
    if(!passwordInput) throw "auth-modal-password element not found";
    const login = loginInput.value;
    let isOk = true
    if(!login || login.includes(":")){
        loginInput.classList.add("is-invalid")
        isOk = false;
    } else {
        loginInput.classList.remove("is-invalid")
    }
    const password = passwordInput.value;
    if(!password || password.length < 3){
        passwordInput.classList.add("is-invalid")
        isOk = false;
    } else {
        passwordInput.classList.remove("is-invalid")
    }
    if(isOk){
        //RFC 7617
        let userPass=login + ":" + password;
        let credentials = Base64.encode(userPass);
        
        // Очищуємо alert перед запитом
        const alertDiv = document.getElementById('auth-modal-alert');
        const alertMsg = document.getElementById('auth-modal-alert-msg');
        alertDiv.classList.add('d-none');
        alertDiv.classList.remove('alert-danger', 'alert-success');
        alertMsg.textContent = '';
        
        fetch("/auth/", {
            headers: {
                "Authorization": "Basic " + credentials
            }
        })
        .then(async r => {
            // Завжди видалямо d-none для показу alert
            alertDiv.classList.remove('d-none');
            
            if (r.status === 401) {
                alertMsg.textContent = 'Невірний логін або пароль';
                alertDiv.classList.add('alert-danger');
                alertDiv.classList.remove('alert-success');
            } else if (r.status === 204) {
                alertMsg.textContent = 'Успішна автентифікація';
                alertDiv.classList.add('alert-success');
                alertDiv.classList.remove('alert-danger');
            } else if (r.status >= 500) {
                alertMsg.textContent = `Помилка сервера: ${r.status}`;
                alertDiv.classList.add('alert-danger');
                alertDiv.classList.remove('alert-success');
            } else if (r.status === 200) {
                alertMsg.textContent = `HTTP ${r.status}`;
                alertDiv.classList.add('alert-success');
                alertDiv.classList.remove('alert-danger');
            } else {
                alertMsg.textContent = `HTTP ${r.status}`;
                alertDiv.classList.add('alert-danger');
                alertDiv.classList.remove('alert-success');
            }
            console.log(`Auth status: ${r.status}`);
            
            // Закриваємо модальне вікно при успішній автентифікації
            if(r.ok) {
                r.text().then(t => {
                    window.auth_token = t;
                    var myModalEl = document.getElementById('authModal');
                    var modal = bootstrap.Modal.getInstance(myModalEl);
                    modal.hide();
                });
            } else {
                r.text().then(alert);
            }
        })
        .catch(err => {
            alertDiv.classList.remove('d-none');
            alertDiv.classList.add('alert-danger');
            alertDiv.classList.remove('alert-success');
            alertMsg.textContent = 'Помилка запиту: ' + err.message;
            console.error('Auth error:', err);
        });
    }
}

function btnSeedClick() {
    if(confirm("Це вельми небезпечна дія. Підтверджуєте?")) {
        fetch("/seed/", {
            method: "PATCH"
        })
        .then(r => {
            if (!r.ok) {
                return r.text().then(t => { throw new Error(`HTTP ${r.status}: ${t.substring(0,200)}`); });
            }
            return r.json();
        })
        .then(j => {
            console.log(j);
        })
        .catch(err => {
            console.error('Seed error:', err);
            alert('Ошибка при выполнении seed: ' + err.message);
        });
    }
}