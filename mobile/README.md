# SetuStock Mobile (Android / iOS)

React Native mobile client for SetuStock field sales, order/customer lookup, delivery visibility, offline queue sync and the business assistant.

## Stack

- Expo SDK 57 (stable baseline in September 2026)
- React Native 0.86
- React 19.2.3
- AsyncStorage 2.2.0 for mobile session/offline queue persistence

## Run

```bash
cd mobile
npm install
npx expo install --fix
EXPO_PUBLIC_API_URL=http://YOUR-LAN-IP:8000/api npm start
```

For a phone, `127.0.0.1` points at the phone itself. Use the development machine's LAN IP or a deployed HTTPS API.

## Production checklist

Use an HTTPS API, EAS development builds, real Android/iOS package identifiers, secure secret handling, push notification credentials, crash monitoring, privacy disclosures, store screenshots/metadata, and device testing before store submission.
