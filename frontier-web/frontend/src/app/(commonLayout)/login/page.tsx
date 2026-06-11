// src/app/login/page.tsx
import LoginForm from '@/components/auth/LoginForm'
import Image from 'next/image'
import Link from 'next/link'

export default function LoginPage() {
  return (
    <div className="min-h-screen flex justify-center w-full">

      <div className="w-full flex mt-32 px-8 py-16 md:px-16 lg:px-24">
        <LoginForm />
      </div>
    </div>
  )
}