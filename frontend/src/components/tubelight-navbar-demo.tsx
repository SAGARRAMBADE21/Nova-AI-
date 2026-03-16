import { Home, User, FileText, Settings } from 'lucide-react'
import { NavBar } from "@/components/ui/tubelight-navbar"

export function NavBarDemo() {
  const navItems = [
    { name: 'Overview', url: '/dashboard/overview', icon: Home },
    { name: 'Documents', url: '/dashboard/documents', icon: FileText },
    { name: 'Users', url: '/dashboard/users', icon: User },
    { name: 'Settings', url: '/dashboard/settings', icon: Settings }
  ]

  return <NavBar items={navItems} />
}
