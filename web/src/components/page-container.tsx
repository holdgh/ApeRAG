'use client';

import { cn } from '@/lib/utils';
import React from 'react';

export type AppTopbarBreadcrumbItem = {
  title: string;
  href?: string;
};

export const PageHeader = () => {
  return;
};

export const PageTitle = ({
  className,
  ...props
}: React.ComponentProps<'h1'>) => {
  return <h1 className={cn('text-2xl font-medium', className)} {...props} />;
};

export const PageDescription = ({
  className,
  ...props
}: React.ComponentProps<'div'>) => {
  return (
    <div className={cn('text-muted-foreground mb-4', className)} {...props} />
  );
};

export const PageContent = ({
  className,
  ...props
}: React.ComponentProps<'div'>) => {
  return <div className={cn('mx-auto max-w-6xl p-4', className)} {...props} />;
};

export const PageContainer = ({
  className,
  ...props
}: React.ComponentProps<'div'>) => {
  return <div className={cn('', className)} {...props} />;
};
