import AsyncStorage from '@react-native-async-storage/async-storage';
const API=process.env.EXPO_PUBLIC_API_URL||'http://127.0.0.1:8000/api';
export async function login(email,password){const r=await fetch(`${API}/auth/login/`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email,password})});const j=await r.json();if(!r.ok)throw new Error(j.detail||'Login failed');await AsyncStorage.multiSet([['token',j.token],['refresh',j.refreshToken||''],['user',JSON.stringify(j.user)]]);return j.user}
export async function get(path){const token=await AsyncStorage.getItem('token');const r=await fetch(`${API}/${path.replace(/^\//,'')}`,{headers:{Authorization:`Bearer ${token}`}});const j=await r.json();if(!r.ok)throw new Error(j.detail||'Request failed');return j}
export async function post(path,body){const token=await AsyncStorage.getItem('token');const r=await fetch(`${API}/${path.replace(/^\//,'')}`,{method:'POST',headers:{Authorization:`Bearer ${token}`,'Content-Type':'application/json'},body:JSON.stringify(body)});const j=await r.json();if(!r.ok)throw new Error(j.detail||'Request failed');return j}
export async function restoreUser(){const raw=await AsyncStorage.getItem('user');return raw?JSON.parse(raw):null}
export async function logout(){await AsyncStorage.multiRemove(['token','refresh','user'])}
