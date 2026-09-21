import AsyncStorage from '@react-native-async-storage/async-storage';import {post} from './api';
const KEY='setustock_mobile_queue';
export async function queued(){return JSON.parse(await AsyncStorage.getItem(KEY)||'[]')}
export async function enqueue(type,payload){const q=await queued();q.push({id:`mob-${Date.now()}-${Math.random().toString(16).slice(2)}`,type,payload,createdAt:new Date().toISOString()});await AsyncStorage.setItem(KEY,JSON.stringify(q));return q}
export async function syncQueue(){const q=await queued();if(!q.length)return{synced:0};const r=await post('sync/offline/',{deviceId:'setustock-mobile',events:q});const done=new Set((r.results||[]).filter(x=>['synced','duplicate'].includes(x.status)).map(x=>x.id));const left=q.filter(x=>!done.has(x.id));await AsyncStorage.setItem(KEY,JSON.stringify(left));return{...r,left:left.length}}
