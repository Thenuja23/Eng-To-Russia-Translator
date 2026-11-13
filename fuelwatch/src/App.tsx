import React, { useState, useEffect } from 'react';
import {
  Fuel,
  Gauge,
  MapPin,
  TrendingUp,
  AlertTriangle,
  Building2,
  ShieldCheck,
  Search,
  RefreshCw,
  Bell,
  CheckCircle2,
  XCircle,
  Truck,
  Droplets,
  DollarSign,
  BarChart3,
  Layers,
  Settings,
  Languages,
  Zap,
  ChevronRight,
  Info,
  Clock,
  Radio,
  Sliders
} from 'lucide-react';

// Translations dictionary for Public Driver view
const translations = {
  EN: {
    title: "FuelWatch Lanka",
    tagline: "Real-time petrol station tank monitoring for Sri Lanka",
    searchPlaceholder: "Search town, city or station name...",
    allGrades: "All Fuel Types",
    petrol92: "Petrol 92",
    petrol95: "Petrol 95",
    diesel: "Auto Diesel",
    superDiesel: "Super Diesel",
    available: "Available",
    limited: "Limited Stock",
    outOfStock: "Out of Stock",
    queueTime: "Est. Queue",
    lastUpdated: "Last sensor ping",
    nextBowser: "Next Bowser ETA",
    reportIssue: "Report Status",
    stationDetails: "Station Details",
    viewMap: "View Map View"
  },
  SI: {
    title: "ෆිවුඅල්වොච් ලංකා",
    tagline: "ශ්‍රී ලංකාවේ පිරවුම්හල් තත්‍ය කාලීන ඉන්ධන මට්ටම් නිරීක්ෂණය",
    searchPlaceholder: "නගරය හෝ පිරවුම්හල සොයන්න...",
    allGrades: "සියලු ඉන්ධන වර්ග",
    petrol92: "පෙට්‍රල් 92",
    petrol95: "පෙට්‍රල් 95",
    diesel: "ඔටෝ ඩීසල්",
    superDiesel: "සුපිරි ඩීසල්",
    available: "ඇත",
    limited: "සීමිතයි",
    outOfStock: "අවසන් වී ඇත",
    queueTime: "පෝලිම් කාලය",
    lastUpdated: "අවසන් යාවත්කාලීනය",
    nextBowser: "ඊළඟ බවුසරය පැමිණීම",
    reportIssue: "තොරතුරු වාර්තා කරන්න",
    stationDetails: "විස්තර",
    viewMap: "සිතියම"
  },
  TA: {
    title: "ஃபியூயல்வாட்ச் இலங்கை",
    tagline: "இலங்கைக்கான நிகழ்நேர எரிபொருள் நிலைய தொட்டி கண்காணிப்பு",
    searchPlaceholder: "நகரம் அல்லது நிலையத்தைத் தேடுங்கள்...",
    allGrades: "அனைத்து எரிபொருள் வகைகள்",
    petrol92: "பெட்ரோல் 92",
    petrol95: "பெட்ரோல் 95",
    diesel: "ஆட்டோ டீசல்",
    superDiesel: "சூப்பர் டீசல்",
    available: "கிடைக்கும்",
    limited: "குறைவாக உள்ளது",
    outOfStock: "இருப்பு இல்லை",
    queueTime: "வரிசை நேரம்",
    lastUpdated: "கடைசி புதுப்பிப்பு",
    nextBowser: "அடுத்த போசர் நேரம்",
    reportIssue: "அறிக்கை செய்க",
    stationDetails: "விவரங்கள்",
    viewMap: "வரைபடம்"
  }
};

// Initial Stations Mock Data
const initialStations = [
  {
    id: "st-101",
    name: "Ceypetco - Town Hall",
    company: "Ceypetco",
    location: "Colombo 07",
    district: "Colombo",
    province: "Western",
    address: "F. R. Senanayake Mawatha, Colombo 07",
    status: "Operational",
    queueMins: 15,
    lastPing: "Just now",
    bowserEta: "Today 14:30 (13,200L Petrol 92)",
    tanks: [
      { id: "t1", grade: "Petrol 92", capacity: 20000, currentLitres: 14200, temp: 28.4, status: "Normal", pumpActive: true },
      { id: "t2", grade: "Petrol 95", capacity: 15000, currentLitres: 8500, temp: 28.1, status: "Normal", pumpActive: true },
      { id: "t3", grade: "Auto Diesel", capacity: 25000, currentLitres: 19800, temp: 29.0, status: "Normal", pumpActive: true },
      { id: "t4", grade: "Super Diesel", capacity: 12000, currentLitres: 2100, temp: 28.7, status: "Low Warning", pumpActive: true }
    ]
  },
  {
    id: "st-102",
    name: "Lanka IOC - Kollupitiya",
    company: "Lanka IOC",
    location: "Colombo 03",
    district: "Colombo",
    province: "Western",
    address: "Galle Road, Kollupitiya",
    status: "Operational",
    queueMins: 5,
    lastPing: "2 mins ago",
    bowserEta: "Tomorrow 09:00",
    tanks: [
      { id: "t1", grade: "Petrol 92", capacity: 22000, currentLitres: 18400, temp: 27.9, status: "Normal", pumpActive: true },
      { id: "t2", grade: "Petrol 95", capacity: 18000, currentLitres: 12100, temp: 28.0, status: "Normal", pumpActive: true },
      { id: "t3", grade: "Auto Diesel", capacity: 22000, currentLitres: 4500, temp: 28.5, status: "Low Warning", pumpActive: true },
      { id: "t4", grade: "Super Diesel", capacity: 10000, currentLitres: 6800, temp: 28.2, status: "Normal", pumpActive: true }
    ]
  },
  {
    id: "st-103",
    name: "Sinopec - Nugegoda",
    company: "Sinopec",
    location: "Nugegoda",
    district: "Colombo",
    province: "Western",
    address: "High Level Road, Nugegoda",
    status: "Operational",
    queueMins: 0,
    lastPing: "1 min ago",
    bowserEta: "En Route (25 mins away)",
    tanks: [
      { id: "t1", grade: "Petrol 92", capacity: 25000, currentLitres: 21000, temp: 27.5, status: "Normal", pumpActive: true },
      { id: "t2", grade: "Petrol 95", capacity: 15000, currentLitres: 13500, temp: 27.6, status: "Normal", pumpActive: true },
      { id: "t3", grade: "Auto Diesel", capacity: 30000, currentLitres: 27000, temp: 28.1, status: "Normal", pumpActive: true },
      { id: "t4", grade: "Super Diesel", capacity: 15000, currentLitres: 11200, temp: 27.9, status: "Normal", pumpActive: true }
    ]
  },
  {
    id: "st-104",
    name: "RM Parks / Shell - Kandy City",
    company: "RM Parks / Shell",
    location: "Kandy",
    district: "Kandy",
    province: "Central",
    address: "Peradeniya Road, Kandy",
    status: "Operational",
    queueMins: 25,
    lastPing: "4 mins ago",
    bowserEta: "Today 18:00",
    tanks: [
      { id: "t1", grade: "Petrol 92", capacity: 20000, currentLitres: 2500, temp: 26.8, status: "Low Warning", pumpActive: true },
      { id: "t2", grade: "Petrol 95", capacity: 12000, currentLitres: 800, temp: 26.5, status: "Critical Low", pumpActive: false },
      { id: "t3", grade: "Auto Diesel", capacity: 20000, currentLitres: 11000, temp: 27.0, status: "Normal", pumpActive: true },
      { id: "t4", grade: "Super Diesel", capacity: 10000, currentLitres: 5400, temp: 26.9, status: "Normal", pumpActive: true }
    ]
  },
  {
    id: "st-105",
    name: "United Petroleum - Galle Fort Entrance",
    company: "United Petroleum",
    location: "Galle",
    district: "Galle",
    province: "Southern",
    address: "Main Street, Galle",
    status: "Operational",
    queueMins: 10,
    lastPing: "Just now",
    bowserEta: "Scheduled for 22 Oct 2026",
    tanks: [
      { id: "t1", grade: "Petrol 92", capacity: 22000, currentLitres: 15000, temp: 29.1, status: "Normal", pumpActive: true },
      { id: "t2", grade: "Petrol 95", capacity: 10000, currentLitres: 4200, temp: 29.3, status: "Normal", pumpActive: true },
      { id: "t3", grade: "Auto Diesel", capacity: 25000, currentLitres: 18900, temp: 29.8, status: "Normal", pumpActive: true },
      { id: "t4", grade: "Super Diesel", capacity: 10000, currentLitres: 200, temp: 29.5, status: "Empty", pumpActive: false }
    ]
  }
];

export default function App() {
  // Navigation role state
  const [activeRole, setActiveRole] = useState('driver'); // 'driver' | 'station' | 'dealer' | 'government'
  const [lang, setLang] = useState('EN'); // 'EN' | 'SI' | 'TA'
  
  // App Shared State
  const [stations, setStations] = useState(initialStations);
  const [selectedStationId, setSelectedStationId] = useState('st-101');
  const [filterGrade, setFilterGrade] = useState('All');
  const [searchQuery, setSearchQuery] = useState('');
  
  // Dealer Financial Model Dynamic Controls
  const [simStationCount, setSimStationCount] = useState(120);
  const [subscriptionTier, setSubscriptionTier] = useState('Pro'); // 'Basic', 'Pro', 'Gold'
  
  // Alert Logs
  const [alertsLog, setAlertsLog] = useState([
    { id: 1, time: '10:42 AM', station: 'Ceypetco - Town Hall', tank: 'Super Diesel', type: 'Low Stock Alert', msg: 'Tank level below 20% (2,100L remaining)' },
    { id: 2, time: '09:15 AM', station: 'RM Parks / Shell - Kandy City', tank: 'Petrol 95', type: 'Pump Deactivated', msg: 'Pump auto-disabled due to low heel limit' }
  ]);

  const selectedStation = stations.find(s => s.id === selectedStationId) || stations[0];
  const t = translations[lang];

  // Helper function to calculate fuel percentage
  const getPercent = (current, capacity) => Math.round((current / capacity) * 100);

  // Status color pill helper
  const getStatusColor = (percent) => {
    if (percent <= 5) return { bg: 'bg-red-500', text: 'text-red-500', badge: 'bg-red-100 text-red-800 border-red-300', label: 'Empty / Critical' };
    if (percent < 25) return { bg: 'bg-amber-500', text: 'text-amber-500', badge: 'bg-amber-100 text-amber-800 border-amber-300', label: 'Low Stock' };
    if (percent < 60) return { bg: 'bg-blue-500', text: 'text-blue-500', badge: 'bg-blue-100 text-blue-800 border-blue-300', label: 'Medium' };
    return { bg: 'bg-emerald-500', text: 'text-emerald-500', badge: 'bg-emerald-100 text-emerald-800 border-emerald-300', label: 'Sufficient / Full' };
  };

  // Trigger Simulation: Dispense Fuel / Sudden Drop / Bowser Delivery
  const handleSimulateFuelDrop = (tankGrade, amountLitres) => {
    setStations(prev => prev.map(st => {
      if (st.id === selectedStationId) {
        return {
          ...st,
          tanks: st.tanks.map(tk => {
            if (tk.grade === tankGrade) {
              const newLitres = Math.max(0, tk.currentLitres - amountLitres);
              return { ...tk, currentLitres: newLitres };
            }
            return tk;
          })
        };
      }
      return st;
    }));
  };

  const handleSimulateDelivery = (tankGrade, amountLitres) => {
    setStations(prev => prev.map(st => {
      if (st.id === selectedStationId) {
        return {
          ...st,
          tanks: st.tanks.map(tk => {
            if (tk.grade === tankGrade) {
              const newLitres = Math.min(tk.capacity, tk.currentLitres + amountLitres);
              return { ...tk, currentLitres: newLitres };
            }
            return tk;
          })
        };
      }
      return st;
    }));

    setAlertsLog(prev => [
      {
        id: Date.now(),
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        station: selectedStation.name,
        tank: tankGrade,
        type: 'Delivery Confirmed',
        msg: `Bowser refilled +${amountLitres.toLocaleString()} Litres into tank.`
      },
      ...prev
    ]);
  };

  const handleSimulateTheftAlert = () => {
    // Drop selected station first tank by 1500L abruptly
    const targetTank = selectedStation.tanks[0];
    handleSimulateFuelDrop(targetTank.grade, 1500);

    setAlertsLog(prev => [
      {
        id: Date.now(),
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        station: selectedStation.name,
        tank: targetTank.grade,
        type: 'SUDDEN DROP / THEFT ALERT',
        msg: `Sudden drop of 1,500L detected without active dispenser pulses!`
      },
      ...prev
    ]);
  };

  const handleTogglePump = (tankGrade) => {
    setStations(prev => prev.map(st => {
      if (st.id === selectedStationId) {
        return {
          ...st,
          tanks: st.tanks.map(tk => {
            if (tk.grade === tankGrade) {
              return { ...tk, pumpActive: !tk.pumpActive };
            }
            return tk;
          })
        };
      }
      return st;
    }));
  };

  // Filtered stations for driver view
  const filteredStations = stations.filter(st => {
    const matchesSearch = st.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
                          st.location.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          st.district.toLowerCase().includes(searchQuery.toLowerCase());
    
    if (filterGrade === 'All') return matchesSearch;
    const tank = st.tanks.find(t => t.grade === filterGrade);
    return matchesSearch && tank && (tank.currentLitres / tank.capacity) > 0.05;
  });

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col font-sans">
      
      {/* GLOBAL TOP HEADER / NAVIGATION */}
      <header className="bg-slate-950 border-b border-slate-800 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto min-w-0 px-3 sm:px-4 py-3 flex flex-col md:flex-row md:items-center justify-between gap-3 md:gap-4">
          
          {/* Brand Logo */}
          <div className="flex items-center space-x-3">
            <div className="bg-gradient-to-tr from-emerald-500 to-teal-400 p-2.5 rounded-xl shadow-lg shadow-emerald-500/20 text-slate-950 font-bold">
              <Fuel className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-extrabold text-xl tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white via-slate-200 to-emerald-400">
                  FuelWatch Lanka
                </span>
                <span className="bg-emerald-500/10 text-emerald-400 text-xs px-2 py-0.5 rounded-full font-semibold border border-emerald-500/20 flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span> LIVE IOT
                </span>
              </div>
              <p className="text-xs text-slate-400">Real-time petrol station tank monitoring</p>
            </div>
          </div>

          {/* Role Switcher Tabs */}
          <div className="fw-horizontal-scroll min-w-0 w-full md:w-auto flex items-center gap-0.5 bg-slate-900 p-1.5 rounded-xl border border-slate-800 overflow-x-auto">
            <button
              onClick={() => setActiveRole('driver')}
              className={`shrink-0 min-h-10 flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs md:text-sm font-medium transition-all whitespace-nowrap ${
                activeRole === 'driver' 
                  ? 'bg-emerald-500 text-slate-950 shadow-md font-semibold' 
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
              }`}
            >
              <MapPin className="w-4 h-4" />
              <span>Public Driver App</span>
            </button>

            <button
              onClick={() => setActiveRole('station')}
              className={`shrink-0 min-h-10 flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs md:text-sm font-medium transition-all whitespace-nowrap ${
                activeRole === 'station' 
                  ? 'bg-emerald-500 text-slate-950 shadow-md font-semibold' 
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
              }`}
            >
              <Gauge className="w-4 h-4" />
              <span>Station Office Monitor</span>
            </button>

            <button
              onClick={() => setActiveRole('dealer')}
              className={`shrink-0 min-h-10 flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs md:text-sm font-medium transition-all whitespace-nowrap ${
                activeRole === 'dealer' 
                  ? 'bg-emerald-500 text-slate-950 shadow-md font-semibold' 
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
              }`}
            >
              <TrendingUp className="w-4 h-4" />
              <span>Dealer & Business</span>
            </button>

            <button
              onClick={() => setActiveRole('government')}
              className={`shrink-0 min-h-10 flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs md:text-sm font-medium transition-all whitespace-nowrap ${
                activeRole === 'government' 
                  ? 'bg-emerald-500 text-slate-950 shadow-md font-semibold' 
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
              }`}
            >
              <Building2 className="w-4 h-4" />
              <span>National Dashboard</span>
            </button>
          </div>

          {/* Quick Language Toggle (Only shown or prominent for Driver app) */}
          {activeRole === 'driver' && (
            <div className="flex items-center space-x-1 bg-slate-900 p-1 rounded-lg border border-slate-800 self-start md:self-auto">
              <Languages className="w-4 h-4 text-slate-400 ml-1.5" />
              {['EN', 'SI', 'TA'].map((l) => (
                <button
                  key={l}
                  onClick={() => setLang(l)}
                  className={`px-2 py-1 rounded text-xs font-bold transition-all ${
                    lang === l ? 'bg-emerald-500 text-slate-950' : 'text-slate-400 hover:text-white'
                  }`}
                >
                  {l}
                </button>
              ))}
            </div>
          )}

        </div>
      </header>

      {/* MAIN CONTENT VIEW BASED ON ACTIVE ROLE */}
      <main className="flex-1 min-w-0 max-w-7xl w-full mx-auto p-3 sm:p-4 md:p-6 space-y-4 sm:space-y-6">

        {/* ------------------------------------------------------------- */}
        {/* PERSPECTIVE 1: PUBLIC DRIVER APP & MAP                        */}
        {/* ------------------------------------------------------------- */}
        {activeRole === 'driver' && (
          <div className="space-y-6 animate-fadeIn">
            
            {/* Banner & Search controls */}
            <div className="bg-gradient-to-r from-slate-950 via-slate-900 to-slate-950 border border-slate-800 rounded-2xl p-5 md:p-6 shadow-xl">
              <div className="max-w-2xl space-y-4">
                <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">
                  {t.title}
                </h1>
                <p className="text-slate-400 text-sm md:text-base">
                  {t.tagline}
                </p>

                {/* Search and Filters */}
                <div className="flex flex-col sm:flex-row gap-3 pt-2">
                  <div className="relative flex-1">
                    <Search className="w-5 h-5 absolute left-3.5 top-3 text-slate-500" />
                    <input
                      type="text"
                      placeholder={t.searchPlaceholder}
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="w-full bg-slate-900/90 border border-slate-700/80 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white focus:outline-none focus:border-emerald-500 transition-colors"
                    />
                  </div>
                  
                  {/* Grade Selector Dropdown */}
                  <select
                    value={filterGrade}
                    onChange={(e) => setFilterGrade(e.target.value)}
                    className="w-full sm:w-auto sm:min-w-[10rem] bg-slate-900/90 border border-slate-700/80 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-emerald-500"
                  >
                    <option value="All">{t.allGrades}</option>
                    <option value="Petrol 92">{t.petrol92}</option>
                    <option value="Petrol 95">{t.petrol95}</option>
                    <option value="Auto Diesel">{t.diesel}</option>
                    <option value="Super Diesel">{t.superDiesel}</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Layout: Interactive Station List + Selected Map View Card */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              
              {/* Station List */}
              <div className="lg:col-span-7 space-y-4">
                <div className="flex flex-wrap items-center justify-between gap-x-3 gap-y-1 text-xs text-slate-400 font-medium px-1">
                  <span>SHOWING {filteredStations.length} STATIONS NEARBY</span>
                  <span className="flex items-center gap-1"><RefreshCw className="w-3 h-3 animate-spin text-emerald-400" /> Auto-refreshing IoT stream</span>
                </div>

                {filteredStations.map((st) => (
                  <div
                    key={st.id}
                    onClick={() => setSelectedStationId(st.id)}
                    className={`p-5 rounded-2xl border transition-all cursor-pointer ${
                      selectedStationId === st.id 
                        ? 'bg-slate-800/90 border-emerald-500 shadow-xl shadow-emerald-500/5 ring-1 ring-emerald-500/50' 
                        : 'bg-slate-900/70 border-slate-800 hover:border-slate-700 hover:bg-slate-800/50'
                    }`}
                  >
                    <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-2 mb-3">
                      <div className="min-w-0">
                        <div className="flex flex-wrap items-center gap-2">
                          <h3 className="font-bold text-white text-base md:text-lg break-words">{st.name}</h3>
                          <span className="shrink-0 text-xs bg-slate-800 text-slate-300 border border-slate-700 px-2 py-0.5 rounded-md">
                            {st.company}
                          </span>
                        </div>
                        <p className="text-xs text-slate-400 mt-0.5">{st.address}</p>
                      </div>

                      <div className="text-left sm:text-right">
                        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                          <Clock className="w-3 h-3" /> Queue ~{st.queueMins} mins
                        </span>
                      </div>
                    </div>

                    {/* Fuel Tank Badges Grid */}
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mt-4">
                      {st.tanks.map((tk) => {
                        const pct = getPercent(tk.currentLitres, tk.capacity);
                        const statusColor = getStatusColor(pct);
                        return (
                          <div key={tk.id} className="bg-slate-950/60 p-2.5 rounded-xl border border-slate-800/80">
                            <div className="text-[11px] font-semibold text-slate-400 truncate">{tk.grade}</div>
                            <div className="flex items-baseline justify-between mt-1">
                              <span className={`text-sm font-extrabold ${statusColor.text}`}>
                                {pct}%
                              </span>
                              <span className="text-[10px] text-slate-500 font-mono">
                                {tk.currentLitres.toLocaleString()}L
                              </span>
                            </div>
                            {/* Level Mini Progress Bar */}
                            <div className="w-full bg-slate-800 h-1.5 rounded-full mt-2 overflow-hidden">
                              <div
                                className={`h-full ${statusColor.bg} transition-all duration-500`}
                                style={{ width: `${pct}%` }}
                              ></div>
                            </div>
                          </div>
                        );
                      })}
                    </div>

                    <div className="mt-4 pt-3 border-t border-slate-800/60 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 text-xs text-slate-400">
                      <span className="flex items-center gap-1.5">
                        <Truck className="w-3.5 h-3.5 text-amber-400" />
                        ETA: {st.bowserEta}
                      </span>
                      <span className="text-slate-500">{t.lastUpdated}: {st.lastPing}</span>
                    </div>
                  </div>
                ))}
              </div>

              {/* Station Detail & Simulated Live Map View Panel */}
              <div className="lg:col-span-5 space-y-4">
                
                {/* Simulated Visual Map Card */}
                <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
                  <div className="bg-slate-950 px-4 py-3 border-b border-slate-800 flex justify-between items-center">
                    <span className="text-xs font-bold text-slate-300 flex items-center gap-1.5">
                      <MapPin className="w-4 h-4 text-emerald-400" /> LIVE GPS MAP PREVIEW
                    </span>
                    <span className="text-[10px] bg-emerald-500/20 text-emerald-400 px-2 py-0.5 rounded font-mono">
                      SRI LANKA
                    </span>
                  </div>

                  {/* Stylized Simulated Map Area */}
                  <div className="h-48 bg-slate-950 relative flex items-center justify-center border-b border-slate-800/80 overflow-hidden">
                    {/* Grid Pattern overlay */}
                    <div className="absolute inset-0 bg-[linear-gradient(to_right,#1e293b_1px,transparent_1px),linear-gradient(to_bottom,#1e293b_1px,transparent_1px)] bg-[size:20px_20px] opacity-30"></div>
                    
                    {/* Simulated Roads */}
                    <div className="absolute w-full h-8 bg-slate-800/80 -rotate-12 top-20 flex items-center justify-around border-y border-slate-700/50">
                      <div className="w-8 h-0.5 bg-yellow-500/80"></div>
                      <div className="w-8 h-0.5 bg-yellow-500/80"></div>
                      <div className="w-8 h-0.5 bg-yellow-500/80"></div>
                    </div>

                    {/* Active Selected Marker */}
                    <div className="relative z-10 flex flex-col items-center animate-bounce">
                      <div className="bg-emerald-500 text-slate-950 px-3 py-1 rounded-full font-bold text-xs shadow-lg shadow-emerald-500/50 flex items-center gap-1">
                        <Fuel className="w-3 h-3" /> {selectedStation.company}
                      </div>
                      <div className="w-3 h-3 bg-emerald-500 rotate-45 -mt-1.5"></div>
                    </div>

                    {/* Location Badge */}
                    <div className="absolute bottom-3 left-3 bg-slate-900/90 border border-slate-700 backdrop-blur-md px-3 py-1.5 rounded-xl text-xs text-slate-300">
                      📍 {selectedStation.address}
                    </div>
                  </div>

                  {/* Station Detailed Status Breakdown */}
                  <div className="p-5 space-y-4">
                    <div>
                      <h2 className="text-xl font-extrabold text-white">{selectedStation.name}</h2>
                      <p className="text-xs text-slate-400">Station ID: {selectedStation.id} • Certified Sensors Installed</p>
                    </div>

                    <div className="space-y-3">
                      <h4 className="text-xs font-bold text-slate-400 tracking-wider uppercase">Live Tank Capacities</h4>

                      {selectedStation.tanks.map((tk) => {
                        const pct = getPercent(tk.currentLitres, tk.capacity);
                        const statusColor = getStatusColor(pct);
                        return (
                          <div key={tk.id} className="bg-slate-950 p-3 rounded-xl border border-slate-800 space-y-2">
                            <div className="flex justify-between items-center">
                              <span className="font-semibold text-sm text-slate-200">{tk.grade}</span>
                              <span className={`text-xs px-2 py-0.5 rounded font-semibold ${statusColor.badge}`}>
                                {statusColor.label}
                              </span>
                            </div>

                            <div className="flex justify-between items-baseline text-xs">
                              <span className="text-slate-400 font-mono">{tk.currentLitres.toLocaleString()} / {tk.capacity.toLocaleString()} Litres</span>
                              <span className="font-bold text-white">{pct}% Full</span>
                            </div>

                            <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                              <div
                                className={`h-full ${statusColor.bg} transition-all duration-500`}
                                style={{ width: `${pct}%` }}
                              ></div>
                            </div>
                          </div>
                        );
                      })}
                    </div>

                    {/* Report / Driver Feedback Action */}
                    <button
                      onClick={() => alert("Thank you! Community status update submitted to moderation queue.")}
                      className="w-full bg-slate-800 hover:bg-slate-700 text-slate-200 py-2.5 rounded-xl text-xs font-bold transition-all border border-slate-700 flex items-center justify-center gap-2"
                    >
                      <Bell className="w-4 h-4 text-emerald-400" />
                      {t.reportIssue} (Confirm Queue/Pumps)
                    </button>
                  </div>
                </div>

              </div>

            </div>
          </div>
        )}

        {/* ------------------------------------------------------------- */}
        {/* PERSPECTIVE 2: STATION OFFICE MONITOR                         */}
        {/* ------------------------------------------------------------- */}
        {activeRole === 'station' && (
          <div className="space-y-6 animate-fadeIn">
            
            {/* Header banner */}
            <div className="bg-slate-950 border border-slate-800 rounded-2xl p-5 flex flex-col md:flex-row justify-between items-start md:items-center gap-4 shadow-xl">
              <div>
                <div className="flex items-center gap-2">
                  <span className="bg-emerald-500/20 text-emerald-400 text-xs px-2.5 py-1 rounded-md font-bold uppercase tracking-wider">
                    Station Office Terminal
                  </span>
                  <span className="text-xs text-slate-400">Electronic Dip Stick System v2.4</span>
                </div>
                <h1 className="text-2xl font-black text-white mt-1">{selectedStation.name}</h1>
                <p className="text-xs text-slate-400">{selectedStation.address} • Hardware Gateway ID: GW-COL-8821</p>
              </div>

              {/* Station selector */}
              <div className="flex items-center gap-3">
                <label className="text-xs text-slate-400 font-semibold">Switch Station:</label>
                <select
                  value={selectedStationId}
                  onChange={(e) => setSelectedStationId(e.target.value)}
                  className="bg-slate-900 border border-slate-700 text-sm text-white px-3 py-2 rounded-xl focus:outline-none focus:border-emerald-500"
                >
                  {stations.map(s => (
                    <option key={s.id} value={s.id}>{s.name}</option>
                  ))}
                </select>
              </div>
            </div>

            {/* Electronic Dip Stick Live Gauges Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {selectedStation.tanks.map((tk) => {
                const pct = getPercent(tk.currentLitres, tk.capacity);
                const statusColor = getStatusColor(pct);

                return (
                  <div key={tk.id} className="bg-slate-900 border border-slate-800 rounded-2xl p-5 flex flex-col justify-between shadow-lg relative overflow-hidden">
                    
                    {/* Top Info */}
                    <div className="space-y-1 z-10">
                      <div className="flex justify-between items-center">
                        <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">{tk.id}</span>
                        <span className={`text-[11px] font-bold px-2 py-0.5 rounded ${statusColor.badge}`}>
                          {statusColor.label}
                        </span>
                      </div>
                      <h3 className="text-lg font-black text-white">{tk.grade}</h3>
                    </div>

                    {/* Sensor Tank Visual Meter */}
                    <div className="my-6 relative flex items-center justify-center">
                      {/* Radial / Tank Container representation */}
                      <div className="w-36 h-36 rounded-full border-4 border-slate-800 relative flex items-center justify-center bg-slate-950 overflow-hidden shadow-inner">
                        {/* Tank Fill Layer */}
                        <div
                          className={`absolute bottom-0 w-full transition-all duration-700 ${statusColor.bg} opacity-80`}
                          style={{ height: `${pct}%` }}
                        ></div>
                        
                        {/* Overlay Readings */}
                        <div className="relative z-10 text-center">
                          <span className="text-3xl font-black text-white drop-shadow-md">{pct}%</span>
                          <span className="block text-[10px] text-slate-300 font-bold uppercase tracking-wider">Level</span>
                        </div>
                      </div>
                    </div>

                    {/* Metrics Footer */}
                    <div className="space-y-3 z-10 bg-slate-950/80 p-3 rounded-xl border border-slate-800">
                      <div className="flex justify-between items-center text-xs">
                        <span className="text-slate-400 flex items-center gap-1"><Droplets className="w-3.5 h-3.5 text-blue-400" /> Volume:</span>
                        <span className="font-mono font-bold text-white">{tk.currentLitres.toLocaleString()} L</span>
                      </div>

                      <div className="flex justify-between items-center text-xs">
                        <span className="text-slate-400 flex items-center gap-1"><Gauge className="w-3.5 h-3.5 text-amber-400" /> Capacity:</span>
                        <span className="font-mono text-slate-300">{tk.capacity.toLocaleString()} L</span>
                      </div>

                      <div className="flex justify-between items-center text-xs">
                        <span className="text-slate-400">Sensor Temp:</span>
                        <span className="font-mono text-slate-300">{tk.temp} °C</span>
                      </div>

                      {/* Manual Pump Override Toggle */}
                      <div className="pt-2 border-t border-slate-800 flex items-center justify-between">
                        <span className="text-[11px] text-slate-400 font-semibold">Dispenser Pump:</span>
                        <button
                          onClick={() => handleTogglePump(tk.grade)}
                          className={`px-2.5 py-1 rounded text-xs font-bold transition-all ${
                            tk.pumpActive 
                              ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 hover:bg-emerald-500/30' 
                              : 'bg-red-500/20 text-red-400 border border-red-500/40 hover:bg-red-500/30'
                          }`}
                        >
                          {tk.pumpActive ? 'ACTIVE' : 'LOCKED'}
                        </button>
                      </div>
                    </div>

                  </div>
                );
              })}
            </div>

            {/* Live Interactive Station Test Controls */}
            <div className="bg-slate-950 border border-slate-800 rounded-2xl p-5 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="font-bold text-white text-sm flex items-center gap-2">
                  <Sliders className="w-4 h-4 text-emerald-400" /> SIMULATION CONTROLS (Station Office Test)
                </h3>
                <span className="text-xs text-slate-500">Simulate physical changes in underground tanks</span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <button
                  onClick={() => handleSimulateFuelDrop(selectedStation.tanks[0].grade, 1000)}
                  className="bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 p-3 rounded-xl text-xs font-semibold text-left transition-all flex items-center justify-between"
                >
                  <div>
                    <div className="font-bold text-white">Simulate Sales Dispense</div>
                    <div className="text-[11px] text-slate-400">-1,000L from {selectedStation.tanks[0].grade}</div>
                  </div>
                  <Zap className="w-4 h-4 text-amber-400" />
                </button>

                <button
                  onClick={() => handleSimulateDelivery(selectedStation.tanks[0].grade, 5000)}
                  className="bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 p-3 rounded-xl text-xs font-semibold text-left transition-all flex items-center justify-between"
                >
                  <div>
                    <div className="font-bold text-white">Simulate Bowser Delivery</div>
                    <div className="text-[11px] text-slate-400">+5,000L refill into {selectedStation.tanks[0].grade}</div>
                  </div>
                  <Truck className="w-4 h-4 text-emerald-400" />
                </button>

                <button
                  onClick={handleSimulateTheftAlert}
                  className="bg-red-950/40 hover:bg-red-900/50 border border-red-800/80 text-red-200 p-3 rounded-xl text-xs font-semibold text-left transition-all flex items-center justify-between"
                >
                  <div>
                    <div className="font-bold text-red-400">Trigger Sudden Drop / Theft</div>
                    <div className="text-[11px] text-red-300/80">-1,500L instant anomaly alert</div>
                  </div>
                  <AlertTriangle className="w-4 h-4 text-red-400" />
                </button>
              </div>
            </div>

            {/* Live Station Sensor Logs */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-3">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Bell className="w-4 h-4 text-emerald-400" /> Station Event & Alert Log
              </h3>
              <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                {alertsLog.map(log => (
                  <div key={log.id} className="bg-slate-950 p-3 rounded-xl border border-slate-800/80 flex items-start justify-between text-xs">
                    <div className="space-y-0.5">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-slate-200">{log.type}</span>
                        <span className="text-[10px] bg-slate-800 text-slate-400 px-1.5 py-0.5 rounded">{log.station} • {log.tank}</span>
                      </div>
                      <p className="text-slate-400">{log.msg}</p>
                    </div>
                    <span className="text-[10px] font-mono text-slate-500 whitespace-nowrap">{log.time}</span>
                  </div>
                ))}
              </div>
            </div>

          </div>
        )}

        {/* ------------------------------------------------------------- */}
        {/* PERSPECTIVE 3: DEALER & BUSINESS DASHBOARD                     */}
        {/* ------------------------------------------------------------- */}
        {activeRole === 'dealer' && (
          <div className="space-y-6 animate-fadeIn">
            
            {/* Business Model Overview Header */}
            <div className="bg-slate-950 border border-slate-800 rounded-2xl p-5 md:p-6 shadow-xl space-y-4">
              <div>
                <span className="bg-blue-500/20 text-blue-400 text-xs px-2.5 py-1 rounded-md font-bold uppercase tracking-wider">
                  Commercial Business Model & Analytics
                </span>
                <h1 className="text-2xl font-black text-white mt-2">FuelWatch Lanka Business Dashboard</h1>
                <p className="text-xs text-slate-400 max-w-3xl mt-1">
                  Subscription revenue model, hardware margin calculator, and automated stock reconciliation.
                </p>
              </div>

              {/* Core Financial KPI Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 pt-2">
                <div className="bg-slate-900 p-4 rounded-xl border border-slate-800">
                  <div className="text-xs text-slate-400 font-medium">Blended Monthly Sub / Tank</div>
                  <div className="text-2xl font-extrabold text-white mt-1">LKR 6,000</div>
                  <div className="text-[10px] text-emerald-400 mt-1">Recurring core SAAS revenue</div>
                </div>

                <div className="bg-slate-900 p-4 rounded-xl border border-slate-800">
                  <div className="text-xs text-slate-400 font-medium">Monthly Rev / Station (4 tanks)</div>
                  <div className="text-2xl font-extrabold text-emerald-400 mt-1">LKR 24,000</div>
                  <div className="text-[10px] text-slate-400 mt-1">LKR 20,000 net contribution</div>
                </div>

                <div className="bg-slate-900 p-4 rounded-xl border border-slate-800">
                  <div className="text-xs text-slate-400 font-medium">Hardware Margin / Station</div>
                  <div className="text-2xl font-extrabold text-blue-400 mt-1">LKR 270,000</div>
                  <div className="text-[10px] text-slate-400 mt-1">Sold at cost + 20% to dealer</div>
                </div>

                <div className="bg-slate-900 p-4 rounded-xl border border-slate-800">
                  <div className="text-xs text-slate-400 font-medium">Station Hardware Payback</div>
                  <div className="text-2xl font-extrabold text-white mt-1">Immediate</div>
                  <div className="text-[10px] text-emerald-400 mt-1">Dealer funded (no startup debt)</div>
                </div>
              </div>
            </div>

            {/* Interactive 3-Year Projection Model & Tier Picker */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              
              {/* Interactive Scenario Calculator */}
              <div className="lg:col-span-7 bg-slate-900 border border-slate-800 rounded-2xl p-5 md:p-6 space-y-5">
                <div className="flex justify-between items-center border-b border-slate-800 pb-3">
                  <div>
                    <h3 className="font-bold text-white text-base">3-Year Revenue Scenario Simulator</h3>
                    <p className="text-xs text-slate-400">Adjust active station count to project growth</p>
                  </div>
                  <BarChart3 className="w-5 h-5 text-emerald-400" />
                </div>

                {/* Slider */}
                <div className="space-y-2">
                  <div className="flex justify-between text-xs font-bold">
                    <span className="text-slate-400">Active Installed Stations:</span>
                    <span className="text-emerald-400 font-mono text-base">{simStationCount} Stations</span>
                  </div>
                  <input
                    type="range"
                    min="10"
                    max="500"
                    step="10"
                    value={simStationCount}
                    onChange={(e) => setSimStationCount(Number(e.target.value))}
                    className="w-full accent-emerald-500 bg-slate-800 h-2 rounded-lg cursor-pointer"
                  />
                  <div className="flex justify-between text-[10px] text-slate-500 font-mono">
                    <span>10 (Pilot)</span>
                    <span>120 (Year 2 Target)</span>
                    <span>400+ (Year 3 Target)</span>
                  </div>
                </div>

                {/* Calculated Financial Outputs */}
                <div className="grid grid-cols-2 gap-3 pt-2">
                  <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                    <span className="text-xs text-slate-400">Annual Recurring Subscription</span>
                    <div className="text-xl font-extrabold text-emerald-400 mt-1">
                      LKR {((simStationCount * 24000 * 12) / 1000000).toFixed(1)} M
                    </div>
                  </div>

                  <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                    <span className="text-xs text-slate-400">Total Hardware Margin</span>
                    <div className="text-xl font-extrabold text-blue-400 mt-1">
                      LKR {((simStationCount * 270000) / 1000000).toFixed(1)} M
                    </div>
                  </div>
                </div>

                <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800/80 text-xs text-slate-400 space-y-1">
                  <div className="font-bold text-slate-200">Key Execution Roadmap:</div>
                  <p>• Year 1 (25 Stations): LKR 10.3M Total Rev</p>
                  <p>• Year 2 (120 Stations): LKR 58.5M Total Rev (CPC & Private chains)</p>
                  <p>• Year 3 (400 Stations): LKR 180.5M Total Rev (Island-wide rollout)</p>
                </div>
              </div>

              {/* Subscription Tiers Specification */}
              <div className="lg:col-span-5 bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4">
                <h3 className="font-bold text-white text-base border-b border-slate-800 pb-3">Subscription Tiers</h3>

                <div className="space-y-3">
                  
                  {/* Basic */}
                  <div
                    onClick={() => setSubscriptionTier('Basic')}
                    className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
                      subscriptionTier === 'Basic' ? 'bg-slate-800 border-emerald-500' : 'bg-slate-950 border-slate-800'
                    }`}
                  >
                    <div className="flex justify-between items-center">
                      <span className="font-bold text-white text-sm">Basic Tier</span>
                      <span className="text-xs font-mono font-bold text-emerald-400">LKR 4,000 / tank / mo</span>
                    </div>
                    <p className="text-xs text-slate-400 mt-1">Sensor data + station office monitor view + basic tank levels.</p>
                  </div>

                  {/* Pro */}
                  <div
                    onClick={() => setSubscriptionTier('Pro')}
                    className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
                      subscriptionTier === 'Pro' ? 'bg-slate-800 border-emerald-500' : 'bg-slate-950 border-slate-800'
                    }`}
                  >
                    <div className="flex justify-between items-center">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-white text-sm">Pro Tier</span>
                        <span className="bg-emerald-500 text-slate-950 text-[10px] font-bold px-1.5 py-0.2 rounded">POPULAR</span>
                      </div>
                      <span className="text-xs font-mono font-bold text-emerald-400">LKR 7,000 / tank / mo</span>
                    </div>
                    <p className="text-xs text-slate-400 mt-1">Basic + Theft/leak alerts, automated stock reports, delivery verification.</p>
                  </div>

                  {/* Gold */}
                  <div
                    onClick={() => setSubscriptionTier('Gold')}
                    className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
                      subscriptionTier === 'Gold' ? 'bg-slate-800 border-emerald-500' : 'bg-slate-950 border-slate-800'
                    }`}
                  >
                    <div className="flex justify-between items-center">
                      <span className="font-bold text-white text-sm">Gold Tier</span>
                      <span className="text-xs font-mono font-bold text-emerald-400">LKR 10,000 / tank / mo</span>
                    </div>
                    <p className="text-xs text-slate-400 mt-1">Pro + Public app listing, delivery ETA integration, enterprise API access.</p>
                  </div>

                </div>
              </div>

            </div>

            {/* Daily Reconciliation Log Simulation */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4">
              <div className="flex justify-between items-center">
                <h3 className="font-bold text-white text-sm flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" /> Automated Daily Reconciliation Report
                </h3>
                <span className="text-xs text-slate-400">Station: {selectedStation.name}</span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="bg-slate-950 text-slate-400 border-b border-slate-800">
                      <th className="p-3">Fuel Grade</th>
                      <th className="p-3">Opening Volume</th>
                      <th className="p-3">Dispensed (Sales)</th>
                      <th className="p-3">Bowser Delivered</th>
                      <th className="p-3">Calculated Volume</th>
                      <th className="p-3">Sensor Volume</th>
                      <th className="p-3">Variance / Loss</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 text-slate-300">
                    {selectedStation.tanks.map((tk) => {
                      const opening = tk.currentLitres + 1200;
                      const dispensed = 1200;
                      const calculated = opening - dispensed;
                      const variance = tk.currentLitres - calculated;
                      return (
                        <tr key={tk.id} className="hover:bg-slate-800/40">
                          <td className="p-3 font-semibold text-white">{tk.grade}</td>
                          <td className="p-3 font-mono">{opening.toLocaleString()} L</td>
                          <td className="p-3 font-mono text-amber-400">-{dispensed.toLocaleString()} L</td>
                          <td className="p-3 font-mono text-emerald-400">+0 L</td>
                          <td className="p-3 font-mono">{calculated.toLocaleString()} L</td>
                          <td className="p-3 font-mono font-bold text-white">{tk.currentLitres.toLocaleString()} L</td>
                          <td className="p-3 font-mono font-bold">
                            {variance === 0 ? (
                              <span className="text-emerald-400">0 L (Match)</span>
                            ) : (
                              <span className="text-red-400">{variance} L</span>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>

          </div>
        )}

        {/* ------------------------------------------------------------- */}
        {/* PERSPECTIVE 4: NATIONAL GOVERNMENT DASHBOARD                 */}
        {/* ------------------------------------------------------------- */}
        {activeRole === 'government' && (
          <div className="space-y-6 animate-fadeIn">
            
            {/* Government Overview Header */}
            <div className="bg-slate-950 border border-slate-800 rounded-2xl p-5 md:p-6 shadow-xl space-y-3">
              <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="bg-red-500/20 text-red-400 text-xs px-2.5 py-1 rounded-md font-bold uppercase tracking-wider">
                      Ministry of Power & Energy / CPTSL
                    </span>
                    <span className="text-xs text-slate-400">National Energy Security Monitoring</span>
                  </div>
                  <h1 className="text-2xl font-black text-white mt-1">Sri Lanka National Fuel Inventory Grid</h1>
                </div>

                <div className="bg-slate-900 border border-slate-800 px-4 py-2 rounded-xl flex items-center gap-3">
                  <div className="w-3 h-3 rounded-full bg-emerald-500 animate-pulse"></div>
                  <div>
                    <div className="text-[10px] text-slate-400">Island-wide Tank Status</div>
                    <div className="text-xs font-bold text-white">84.2% Operational Cover</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Provincial Breakdown Overview Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              
              {/* Western Province */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-3">
                <div className="flex justify-between items-center border-b border-slate-800 pb-2">
                  <h3 className="font-bold text-white text-base">Western Province</h3>
                  <span className="bg-emerald-500/10 text-emerald-400 text-xs px-2 py-0.5 rounded font-semibold">Normal</span>
                </div>
                <div className="space-y-2 text-xs">
                  <div className="flex justify-between text-slate-400">
                    <span>Active Stations:</span>
                    <span className="text-white font-mono font-bold">3 Stations Monitored</span>
                  </div>
                  <div className="flex justify-between text-slate-400">
                    <span>Petrol 92 Stock:</span>
                    <span className="text-emerald-400 font-mono font-bold">53,600 L</span>
                  </div>
                  <div className="flex justify-between text-slate-400">
                    <span>Auto Diesel Stock:</span>
                    <span className="text-emerald-400 font-mono font-bold">73,800 L</span>
                  </div>
                </div>
              </div>

              {/* Central Province */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-3">
                <div className="flex justify-between items-center border-b border-slate-800 pb-2">
                  <h3 className="font-bold text-white text-base">Central Province</h3>
                  <span className="bg-amber-500/10 text-amber-400 text-xs px-2 py-0.5 rounded font-semibold">Shortage Warning</span>
                </div>
                <div className="space-y-2 text-xs">
                  <div className="flex justify-between text-slate-400">
                    <span>Active Stations:</span>
                    <span className="text-white font-mono font-bold">1 Station Monitored</span>
                  </div>
                  <div className="flex justify-between text-slate-400">
                    <span>Petrol 95 Stock:</span>
                    <span className="text-amber-400 font-mono font-bold">800 L (Low)</span>
                  </div>
                  <div className="flex justify-between text-slate-400">
                    <span>Auto Diesel Stock:</span>
                    <span className="text-emerald-400 font-mono font-bold">11,000 L</span>
                  </div>
                </div>
              </div>

              {/* Southern Province */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-3">
                <div className="flex justify-between items-center border-b border-slate-800 pb-2">
                  <h3 className="font-bold text-white text-base">Southern Province</h3>
                  <span className="bg-emerald-500/10 text-emerald-400 text-xs px-2 py-0.5 rounded font-semibold">Normal</span>
                </div>
                <div className="space-y-2 text-xs">
                  <div className="flex justify-between text-slate-400">
                    <span>Active Stations:</span>
                    <span className="text-white font-mono font-bold">1 Station Monitored</span>
                  </div>
                  <div className="flex justify-between text-slate-400">
                    <span>Petrol 92 Stock:</span>
                    <span className="text-emerald-400 font-mono font-bold">15,000 L</span>
                  </div>
                  <div className="flex justify-between text-slate-400">
                    <span>Super Diesel Stock:</span>
                    <span className="text-red-400 font-mono font-bold">200 L (Depleted)</span>
                  </div>
                </div>
              </div>

            </div>

            {/* Strategic Emergency Allocation Action Controls */}
            <div className="bg-slate-950 border border-slate-800 rounded-2xl p-5 space-y-4">
              <h3 className="font-bold text-white text-sm flex items-center gap-2">
                <Radio className="w-4 h-4 text-emerald-400" /> Government Allocation & Panic Mitigation Directives
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-slate-900 p-4 rounded-xl border border-slate-800 space-y-2">
                  <div className="font-bold text-white text-xs">Despatch Priority Dispatch</div>
                  <p className="text-xs text-slate-400">
                    Direct CPTSL Kolonnawa & Muthurajawela terminals to auto-assign next bowser run to Kandy City (Central Province).
                  </p>
                  <button
                    onClick={() => alert("Priority Bowser Order #CPTSL-881 dispatched to Central Province.")}
                    className="bg-emerald-500 text-slate-950 font-bold px-3 py-1.5 rounded-lg text-xs mt-2 hover:bg-emerald-400 transition-all"
                  >
                    Dispatch Priority Bowser
                  </button>
                </div>

                <div className="bg-slate-900 p-4 rounded-xl border border-slate-800 space-y-2">
                  <div className="font-bold text-white text-xs">Emergency Public Throttle Mode</div>
                  <p className="text-xs text-slate-400">
                    Optionally mask exact litres in public app during national shortage alerts to prevent panic queuing.
                  </p>
                  <button
                    onClick={() => alert("Public app mode updated: Showing status ranges (Full/Medium/Low) instead of exact Litres.")}
                    className="bg-slate-800 text-slate-200 border border-slate-700 font-bold px-3 py-1.5 rounded-lg text-xs mt-2 hover:bg-slate-700 transition-all"
                  >
                    Toggle Public Data Broadening
                  </button>
                </div>
              </div>
            </div>

          </div>
        )}

      </main>

      {/* FOOTER */}
      <footer className="bg-slate-950 border-t border-slate-800 py-4 mt-auto">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row justify-between items-center text-xs text-slate-500 gap-2">
          <div>
            © 2026 <span className="text-slate-300 font-semibold">FuelWatch Lanka</span>. Confidential prototype.
          </div>
          <div className="flex items-center gap-4">
            <span>Intrinsically Safe Magnetostrictive Sensors</span>
            <span>4G / NB-IoT Telemetry</span>
          </div>
        </div>
      </footer>

    </div>
  );
}
