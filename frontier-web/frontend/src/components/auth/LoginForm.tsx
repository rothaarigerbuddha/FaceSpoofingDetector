// src/components/auth/LoginForm.tsx
'use client'

import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import Link from 'next/link'
import { useState } from 'react'
import { loginUser } from '@/services/auth.service'
import { useRouter } from 'next/navigation'
import AppButton from '../ui/AppButton'

export default function LoginForm() {

    const router = useRouter();

    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        try {
            setError('');
            setIsLoading(true);
            const result = await loginUser({username, password});
            
            if (result.access_token) {
                router.push('/dashboard');
            }
        } catch (error: any) {
            setError(error?.message || "Invalid credentials");
        } finally {
            setIsLoading(false);
        }
    };

  return (
    <div className="max-w-sm w-full mx-auto flex flex-col gap-8">
      {/* Heading */}
      <div className="flex flex-col gap-2">
        <span className="text-[10px] uppercase tracking-[0.25em] text-muted-foreground">
          Welcome back
        </span>
        <h1 className="font-serif text-3xl text-foreground font-normal">
          Sign in to your account
        </h1>
      </div>

      {/* Form */}
      <form className="flex flex-col gap-6" onSubmit={handleSubmit}>
        <div className="flex flex-col gap-2">
          <Label
            htmlFor="username"
            className="text-[10px] uppercase tracking-[0.2em] text-muted-foreground font-light"
          >
            Username
          </Label>
          <Input
            id="username"
            type="text"
            placeholder="Your username"
            autoComplete="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="rounded-none border-0 border-b border-border bg-transparent px-0 py-2 text-sm text-foreground placeholder:text-muted-foreground/50 focus-visible:ring-0 focus-visible:border-foreground transition-colors duration-200"
          />
        </div>

        <div className="flex flex-col gap-2">
          <div className="flex items-center justify-between">
            <Label
              htmlFor="password"
              className="text-[10px] uppercase tracking-[0.2em] text-muted-foreground font-light"
            >
              Password
            </Label>
          </div>
          <Input
            id="password"
            type="password"
            placeholder="Your password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="rounded-none border-0 border-b border-border bg-transparent px-0 py-2 text-sm text-foreground placeholder:text-muted-foreground/50 focus-visible:ring-0 focus-visible:border-foreground transition-colors duration-200"
          />
        </div>

        {error && (
            <p className="text-sm text-red-500 font-light">{error}</p>
        )}

        <AppButton type="submit" size="lg" className="w-full mt-2" disabled={isLoading}>
          {isLoading ? (
            <span className="flex items-center gap-2">
              <svg
                className="animate-spin h-4 w-4"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12" cy="12" r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                />
              </svg>
              Signing in…
            </span>
          ) : (
            'Sign In'
          )}
        </AppButton>
      </form>

      {/* Divider */}
      {/* <div className="flex items-center gap-4">
        <span className="flex-1 h-px bg-border" />
        <span className="text-[10px] uppercase tracking-[0.2em] text-muted-foreground">or</span>
        <span className="flex-1 h-px bg-border" />
      </div> */}

      {/* Sign up */}
      {/* <p className="text-center text-xs text-muted-foreground font-light">
        Don&apos;t have an account?{' '}
        <Link
          href="/register"
          className="text-foreground underline underline-offset-4 hover:opacity-70 transition-opacity"
        >
          Create one
        </Link>
      </p> */}
    </div>
  )
}