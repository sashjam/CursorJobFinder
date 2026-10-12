import axios from 'axios'

export const http = axios.create({
  baseURL: '/api',
  withCredentials: true,
  headers: {
    Accept: 'application/json',
    'X-Requested-With': 'XMLHttpRequest',
  },
})

let csrfReady = false

export async function ensureCsrf(): Promise<void> {
  if (csrfReady) {
    return
  }
  await axios.get('/sanctum/csrf-cookie', { withCredentials: true })
  csrfReady = true
}

http.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401) {
      csrfReady = false
    }
    return Promise.reject(err)
  },
)
