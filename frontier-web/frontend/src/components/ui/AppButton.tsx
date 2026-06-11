// src/components/ui/Button.tsx
import { cn } from '@/lib/utils'
import Link from 'next/link'
import React from 'react'

type ButtonVariant = 'primary' | 'outline' | 'ghost' | 'link'
type ButtonSize = 'sm' | 'md' | 'lg'

interface BaseProps {
  variant?: ButtonVariant
  size?: ButtonSize
  className?: string
  children: React.ReactNode
}

type ButtonAsButton = BaseProps &
  React.ButtonHTMLAttributes<HTMLButtonElement> & { href?: undefined }

type ButtonAsLink = BaseProps & { href: string; target?: string; rel?: string }

type ButtonProps = ButtonAsButton | ButtonAsLink

const variants: Record<ButtonVariant, string> = {
  primary:
    'bg-primary text-primary-foreground hover:opacity-80',
  outline:
    'border border-foreground text-foreground hover:bg-foreground hover:text-background',
  ghost:
    'text-foreground hover:bg-muted',
  link:
    'text-foreground underline-offset-4 hover:underline p-0',
}

const sizes: Record<ButtonSize, string> = {
  sm: 'text-[10px] tracking-[0.2em] px-4 py-2',
  md: 'text-xs tracking-[0.18em] px-6 py-3',
  lg: 'text-xs tracking-[0.18em] px-8 py-4',
}

const base =
  'inline-flex items-center justify-center uppercase font-light transition-all duration-200 cursor-pointer disabled:opacity-40 disabled:pointer-events-none select-none'

export default function AppButton({
  variant = 'primary',
  size = 'md',
  className,
  children,
  ...props
}: ButtonProps) {
  const classes = cn(
    base,
    variant !== 'link' && sizes[size],
    variants[variant],
    className
  )

  if ('href' in props && props.href !== undefined) {
    const { href, target, rel } = props
    return (
      <Link href={href} target={target} rel={rel} className={classes}>
        {children}
      </Link>
    )
  }

  const { ...buttonProps } = props as ButtonAsButton
  return (
    <button className={classes} {...buttonProps}>
      {children}
    </button>
  )
}