import React, { useEffect, useMemo, useState } from 'react'
import { createRoot } from 'react-dom/client'

const eventUrl = import.meta.env.VITE_EVENT_URL || 'http://localhost:8002'
const authUrl = import.meta.env.VITE_AUTH_URL || 'http://localhost:8001'
const bookingUrl = import.meta.env.VITE_BOOKING_URL || 'http://localhost:8003'
const paymentUrl = import.meta.env.VITE_PAYMENT_URL || 'http://localhost:8004'
const ticketUrl = import.meta.env.VITE_TICKET_URL || 'http://localhost:8005'
const analyticsUrl = import.meta.env.VITE_ANALYTICS_URL || 'http://localhost:8007'

function Card({title, children}) {
  return <div style={{border:'1px solid #ddd', borderRadius:12, padding:16, marginBottom:16}}>
    <h2 style={{marginTop:0}}>{title}</h2>{children}
  </div>
}

function App() {
  const [events, setEvents] = useState([])
  const [users, setUsers] = useState([])
  const [tickets, setTickets] = useState([])
  const [analytics, setAnalytics] = useState({})
  const [message, setMessage] = useState('')
  const [token, setToken] = useState('')
  const [selectedEventId, setSelectedEventId] = useState(1)
  const [selectedUserId, setSelectedUserId] = useState(1)

  const [registerForm, setRegisterForm] = useState({name:'Customer Demo', email:`customer${Date.now()}@demo.local`, password:'customer123', role:'customer'})
  const [loginForm, setLoginForm] = useState({email:'admin@eventhub.local', password:'admin123'})
  const [eventForm, setEventForm] = useState({organizer_id:2, title:'Demo Event', description:'Phase 5 demo event', category:'Tech', venue:'Main Hall', city:'Lagos', start_time:'2026-05-01T10:00:00', end_time:'2026-05-01T18:00:00', total_tickets:100, price:25})
  const [bookingForm, setBookingForm] = useState({user_id:1, event_id:1, quantity:1, total_amount:25})

  async function loadAll() {
    const [e,u,t] = await Promise.all([
      fetch(`${eventUrl}/events`).then(r=>r.json()).catch(()=>[]),
      fetch(`${authUrl}/users`).then(r=>r.json()).catch(()=>[]),
      fetch(`${ticketUrl}/tickets`).then(r=>r.json()).catch(()=>[]),
    ])
    setEvents(e); setUsers(u); setTickets(t)
    if (token) {
      fetch(`${analyticsUrl}/analytics/admin/overview`, {headers:{Authorization:`Bearer ${token}`}})
        .then(r=>r.json()).then(setAnalytics).catch(()=>setAnalytics({}))
    }
  }
  useEffect(()=>{ loadAll() }, [token])

  const selectedEvent = useMemo(() => events.find(e => Number(e.id) === Number(selectedEventId)), [events, selectedEventId])
  const userTickets = useMemo(() => tickets.filter(t => Number(t.user_id) === Number(selectedUserId)), [tickets, selectedUserId])

  async function registerUser(e) {
    e.preventDefault()
    const res = await fetch(`${authUrl}/register`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(registerForm)})
    const data = await res.json()
    setMessage(JSON.stringify(data, null, 2))
    loadAll()
  }
  async function login(e) {
    e.preventDefault()
    const res = await fetch(`${authUrl}/login`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(loginForm)})
    const data = await res.json()
    setToken(data.access_token || '')
    setMessage(JSON.stringify(data, null, 2))
  }
  async function createEvent(e) {
    e.preventDefault()
    const payload = {...eventForm, organizer_id:Number(eventForm.organizer_id), total_tickets:Number(eventForm.total_tickets), price:Number(eventForm.price)}
    const res = await fetch(`${eventUrl}/events`, {method:'POST', headers:{'Content-Type':'application/json', Authorization:`Bearer ${token}`}, body:JSON.stringify(payload)})
    const data = await res.json()
    setMessage(JSON.stringify(data, null, 2))
    loadAll()
  }
  async function createBooking(e) {
    e.preventDefault()
    const payload = {...bookingForm, user_id:Number(bookingForm.user_id), event_id:Number(bookingForm.event_id), quantity:Number(bookingForm.quantity), total_amount:Number(bookingForm.total_amount)}
    const res = await fetch(`${bookingUrl}/bookings`, {method:'POST', headers:{'Content-Type':'application/json', Authorization:`Bearer ${token}`}, body:JSON.stringify(payload)})
    const data = await res.json()
    setMessage(JSON.stringify(data, null, 2))
    setTimeout(loadAll, 1500)
  }
  async function simulatePayment() {
    const res = await fetch(`${paymentUrl}/payments`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({booking_id:1, amount:25})})
    const data = await res.json()
    setMessage(JSON.stringify(data, null, 2) + "\nRun payment_success_worker to auto-issue ticket.")
    setTimeout(loadAll, 3000)
  }

  return <div style={{fontFamily:'Arial', maxWidth:1200, margin:'0 auto', padding:24}}>
    <h1>EventHub Phase 5</h1>
    <p>Production-hardening starter with auth, CI, Helm, ArgoCD, and canary examples.</p>
    {message && <pre style={{background:'#f5f5f5', padding:12, borderRadius:8}}>{message}</pre>}

    <div style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap:16}}>
      <Card title="Login for Protected APIs">
        <form onSubmit={login} style={{display:'grid', gap:8}}>
          <input value={loginForm.email} onChange={e=>setLoginForm({...loginForm, email:e.target.value})} placeholder="Email" />
          <input value={loginForm.password} onChange={e=>setLoginForm({...loginForm, password:e.target.value})} placeholder="Password" />
          <button type="submit">Login</button>
        </form>
        <p style={{wordBreak:'break-all'}}>Token loaded: {token ? 'yes' : 'no'}</p>
      </Card>

      <Card title="Register User">
        <form onSubmit={registerUser} style={{display:'grid', gap:8}}>
          <input value={registerForm.name} onChange={e=>setRegisterForm({...registerForm, name:e.target.value})} placeholder="Name" />
          <input value={registerForm.email} onChange={e=>setRegisterForm({...registerForm, email:e.target.value})} placeholder="Email" />
          <input value={registerForm.password} onChange={e=>setRegisterForm({...registerForm, password:e.target.value})} placeholder="Password" />
          <select value={registerForm.role} onChange={e=>setRegisterForm({...registerForm, role:e.target.value})}>
            <option value="customer">customer</option>
            <option value="organizer">organizer</option>
            <option value="admin">admin</option>
          </select>
          <button type="submit">Register</button>
        </form>
      </Card>
    </div>

    <div style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap:16}}>
      <Card title="Organizer Dashboard">
        <form onSubmit={createEvent} style={{display:'grid', gap:8}}>
          <input value={eventForm.organizer_id} onChange={e=>setEventForm({...eventForm, organizer_id:e.target.value})} placeholder="Organizer ID" />
          <input value={eventForm.title} onChange={e=>setEventForm({...eventForm, title:e.target.value})} placeholder="Title" />
          <input value={eventForm.description} onChange={e=>setEventForm({...eventForm, description:e.target.value})} placeholder="Description" />
          <input value={eventForm.category} onChange={e=>setEventForm({...eventForm, category:e.target.value})} placeholder="Category" />
          <input value={eventForm.venue} onChange={e=>setEventForm({...eventForm, venue:e.target.value})} placeholder="Venue" />
          <input value={eventForm.city} onChange={e=>setEventForm({...eventForm, city:e.target.value})} placeholder="City" />
          <input value={eventForm.start_time} onChange={e=>setEventForm({...eventForm, start_time:e.target.value})} placeholder="Start time" />
          <input value={eventForm.end_time} onChange={e=>setEventForm({...eventForm, end_time:e.target.value})} placeholder="End time" />
          <input value={eventForm.total_tickets} onChange={e=>setEventForm({...eventForm, total_tickets:e.target.value})} placeholder="Total tickets" />
          <input value={eventForm.price} onChange={e=>setEventForm({...eventForm, price:e.target.value})} placeholder="Price" />
          <button type="submit">Create Event</button>
        </form>
      </Card>

      <Card title="Checkout">
        <form onSubmit={createBooking} style={{display:'grid', gap:8}}>
          <input value={bookingForm.user_id} onChange={e=>setBookingForm({...bookingForm, user_id:e.target.value})} placeholder="User ID" />
          <input value={bookingForm.event_id} onChange={e=>setBookingForm({...bookingForm, event_id:e.target.value})} placeholder="Event ID" />
          <input value={bookingForm.quantity} onChange={e=>setBookingForm({...bookingForm, quantity:e.target.value})} placeholder="Quantity" />
          <input value={bookingForm.total_amount} onChange={e=>setBookingForm({...bookingForm, total_amount:e.target.value})} placeholder="Total amount" />
          <button type="submit">Reserve Ticket</button>
        </form>
        <button onClick={simulatePayment} style={{marginTop:12}}>Simulate Payment for Booking #1</button>
      </Card>
    </div>

    <Card title="Event Detail">
      <select value={selectedEventId} onChange={e=>setSelectedEventId(e.target.value)} style={{marginBottom:12}}>
        {events.map(e => <option key={e.id} value={e.id}>{e.title}</option>)}
      </select>
      {selectedEvent ? <div>
        <p><strong>{selectedEvent.title}</strong></p>
        <p>{selectedEvent.city} • {selectedEvent.venue}</p>
        <p>Available tickets: {selectedEvent.available_tickets}</p>
        <p>Price: ${selectedEvent.price}</p>
      </div> : <p>No event selected</p>}
    </Card>

    <Card title="My Tickets">
      <select value={selectedUserId} onChange={e=>setSelectedUserId(e.target.value)} style={{marginBottom:12}}>
        {users.map(u => <option key={u.id} value={u.id}>{u.name}</option>)}
      </select>
      <ul>
        {userTickets.map(t => (
          <li key={t.id}>
            {t.ticket_code} - booking {t.booking_id} - <a href={`${ticketUrl}/tickets/${t.id}/pdf`} target="_blank">PDF</a>
          </li>
        ))}
      </ul>
    </Card>

    <Card title="Admin Overview">
      <pre>{JSON.stringify(analytics, null, 2)}</pre>
    </Card>
  </div>
}

createRoot(document.getElementById('root')).render(<App />)
