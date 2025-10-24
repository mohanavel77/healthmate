
// Basic client-side helpers
function api(path, method='GET', body){
  return fetch(path, {
    method, headers: {'Content-Type':'application/json'},
    body: body? JSON.stringify(body): undefined
  }).then(r=>r.json());
}
