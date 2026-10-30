/* Freestanding AArch64 runtime. Built once into PIC blobs, never compiled by
 * the installed compiler. All mutable state belongs to this process in x27. */
typedef unsigned long U;
typedef long I;
typedef struct { U pool[10],live,debug,top,bottom,error,argv,argc; } State;
#define R(name) U ar_##name(U a,U b,U c,State *s)
#define UNUSED (void)a;(void)b;(void)c;(void)s
#ifdef ARM_MACOS
extern I os_read(I,void*,U),os_write(I,const void*,U);
extern int os_close(int),os_fsync(int);
extern void *os_mmap(void*,U,int,int,int,I);
extern int os_munmap(void*,U),os_nanosleep(void*,void*),os_clock_gettime(int,void*);
extern int os_rename(const char*,const char*),os_unlink(const char*),os_open(const char*,int,int);
extern int *os___error(void);
extern void os__exit(int);
static I result(I v){return v==-1?-(I)*os___error():v;}
static I rd(I fd,void*p,U n){return result(os_read(fd,p,n));}
static I wr(I fd,const void*p,U n){return result(os_write(fd,p,n));}
static void *map(U n){void*p=os_mmap((void*)0,n,3,0x1002,-1,0);return p==(void*)-1?0:p;}
static void unmap(void*p,U n){os_munmap(p,n);}
static void quit(int n){os__exit(n);__builtin_unreachable();}
#else
static I sys(U n,U a,U b,U c,U d,U e,U f){
    register U x0 __asm__("x0")=a,x1 __asm__("x1")=b,x2 __asm__("x2")=c;
    register U x3 __asm__("x3")=d,x4 __asm__("x4")=e,x5 __asm__("x5")=f,x8 __asm__("x8")=n;
    __asm__ volatile("svc #0":"+r"(x0):"r"(x1),"r"(x2),"r"(x3),"r"(x4),"r"(x5),"r"(x8):"memory","cc");return (I)x0;
}
static I rd(I fd,void*p,U n){return sys(63,fd,(U)p,n,0,0,0);}
static I wr(I fd,const void*p,U n){return sys(64,fd,(U)p,n,0,0,0);}
static void *map(U n){I p=sys(222,0,n,3,34,-1,0);return (U)p>=(U)-4095?0:(void*)p;}
static void unmap(void*p,U n){sys(215,(U)p,n,0,0,0,0);}
static void quit(int n){sys(93,(U)n,0,0,0,0,0);__builtin_unreachable();}
#endif
static U length(const char*p){U n=0;if(p)while(p[n])n++;return n;}
static void output(U fd,const void*p,U n){while(n){I v=wr(fd,p,n);if(v==-4)continue;if(v<=0)return;p=(const char*)p+v;n-=(U)v;}}
static void text(U fd,const char*p){output(fd,p,length(p));}
static void number(U fd,U n,int sign){char buf[32];U k=32;do{buf[--k]=(char)('0'+n%10);n/=10;}while(n);if(sign)buf[--k]='-';output(fd,buf+k,32-k);}
static void error(U reason,U site){
    static const char messages[][80]={"retorno ausente\n","acesso a ponteiro/objeto nulo\n","divisão por zero\n","deslocamento deve estar entre 0 e 63\n","tamanho de alocação inválido\n","memória insuficiente\n","índice de texto fora do limite\n","retorno ausente\n","resto por zero\n","índice de array fora do limite\n","assert falhou\n","limite seguro da pilha excedido\n","free duplo ou bloco invalido\n","blocos alocados não liberados\n"};
    text(2,"assis: erro R001, linha ");if(site>>63)text(2,(const char*)(site&~(1UL<<63)));else number(2,site,0);text(2,": ");text(2,messages[reason<14?reason:0]);quit(70);
}
R(init){UNUSED;State*p=map(4096);if(!p)error(5,0);p->top=a;p->bottom=a-4194304;return (U)p;}
R(exit){UNUSED;quit((int)a);return 0;}
R(error){UNUSED;error(a,b);return 0;}
R(write){UNUSED;output(a,(void*)b,c);return 0;}
R(print_str){UNUSED;text(b,(char*)a);return 0;}
R(print_int){UNUSED;number(b,(I)a<0?0-a:a,(I)a<0);return 0;}
R(print_uint){UNUSED;number(b,a,0);return 0;}
R(print_char){UNUSED;char ch=(char)a;output(b,&ch,1);return 0;}
R(print_bool){UNUSED;text(b,a?"true":"false");return 0;}
R(print_ptr){UNUSED;char buf[18]={'0','x'};const char*hex="0123456789abcdef";for(int k=17;k>=2;k--){buf[k]=hex[a&15];a>>=4;}output(b,buf,18);return 0;}
R(print_float){
    UNUSED;char buf[64];U n=0;const char*hex="0123456789abcdef";if(a>>63)buf[n++]='-';U exp=(a>>52)&2047,frac=a&((1UL<<52)-1);
    if(exp==2047){const char*p=frac?"nan":"inf";for(int k=0;k<3;k++)buf[n++]=p[k];}
    else{buf[n++]='0';buf[n++]='x';buf[n++]=exp?'1':'0';buf[n++]='.';for(int k=12;k>=0;k--)buf[n++]=hex[(frac>>(k*4))&15];buf[n++]='p';I e=exp?(I)exp-1023:frac?-1022:0;buf[n++]=e<0?'-':'+';U v=e<0?-e:e;char tail[8];U t=0;do{tail[t++]=(char)('0'+v%10);v/=10;}while(v);while(t)buf[n++]=tail[--t];}output(b,buf,n);return 0;
}
static U allocate(U a,State*s){
    if((I)a<0||a>0x7fffffffffffffdfUL)return 0;U cls=0,size=64;while(size<a+32&&cls<10){size*=2;cls++;}U*p;
    if(cls==10){p=map(a+32);if(!p)return 0;p[0]=a+32;p[1]=10;}
    else{if(!s->pool[cls]){char*slab=map(65536);if(!slab)return 0;for(U off=0;off<65536;off+=size){U*q=(U*)(slab+off);q[0]=size;q[1]=cls;q[2]=off+size<65536?(U)(slab+off+size):0;q[3]=0x46524545;}s->pool[cls]=(U)slab;}p=(U*)s->pool[cls];s->pool[cls]=p[2];char*q=(char*)(p+4);for(U i=0;i<a;i++)q[i]=0;}
    p[2]=a;p[3]=0x41534953;s->live++;return (U)(p+4);
}
R(try_alloc){UNUSED;return allocate(a,s);}
R(alloc){UNUSED;if((I)a<0||a>0x7fffffffffffffdfUL)error(4,b);U p=allocate(a,s);if(!p)error(5,b);return p;}
R(free){
    UNUSED;if(!a)return 0;U*p=(U*)a-4;if(p[3]!=0x41534953)error(12,0);p[3]=0x46524545;s->live--;if(p[1]==10){if(!s->debug)unmap(p,p[0]);return 0;}if(s->debug){char*q=(char*)a;for(U i=0;i<p[2];i++)q[i]=(char)0xdd;}p[2]=s->pool[p[1]];s->pool[p[1]]=(U)p;return 0;
}
R(finish){UNUSED;if(s->debug&&s->live)error(13,0);return 0;}
R(len){UNUSED;return length((char*)a);}
R(streq){UNUSED;if(a==b)return 1;if(!a||!b)return 0;char*p=(char*)a,*q=(char*)b;while(*p&&*p==*q){p++;q++;}return *p==*q;}
R(strbyte){UNUSED;if((I)b<0||b>=length((char*)a))error(6,c);return ((unsigned char*)a)[b];}
static U io(State*s,I value){if(value<0){s->error=(U)-value;return (U)-1;}s->error=0;return (U)value;}
static U invalid(State*s){s->error=22;return (U)-1;}
R(read){UNUSED;if((I)b<0)error(4,c);if(!b)return 0;if(!a)error(1,c);if(b>0x7fffffff)b=0x7fffffff;I v;do{v=rd(0,(void*)a,b);}while(v==-4);return v<0?(U)-1:(U)v;}
static I clocktime(U which,I*t){
#ifdef ARM_MACOS
    return result(os_clock_gettime(which?6:0,t));
#else
    return sys(113,which,(U)t,0,0,0,0);
#endif
}
R(now){UNUSED;I t[2];if(clocktime(1,t)<0)return (U)-1;return (U)t[0]*1000+(U)t[1]/1000000;}
R(civil){UNUSED;I t[2];I v=clocktime(0,t);if(v<0)return io(s,v);s->error=0;return (U)t[0]*1000+(U)t[1]/1000000;}
R(sleep){UNUSED;if(a>0x7fffffff)return invalid(s);I t[2]={(I)(a/1000),(I)(a%1000)*1000000},remain[2],v;do{
#ifdef ARM_MACOS
    v=result(os_nanosleep(t,remain));
#else
    v=sys(101,(U)t,(U)remain,0,0,0,0);
#endif
    if(v==-4){t[0]=remain[0];t[1]=remain[1];}
    }while(v==-4);return io(s,v);}
R(args_init){UNUSED;s->argc=a;s->argv=b;return 0;}
R(argc){UNUSED;return s->argc;}
R(io_error){UNUSED;return s->error;}
R(arg_len){UNUSED;if(a>=s->argc)return invalid(s);s->error=0;return length(((char**)s->argv)[a]);}
R(arg_copy){UNUSED;U n=ar_arg_len(a,0,0,s);if(n==(U)-1)return n;if(!b||c<=n)return invalid(s);char*p=((char**)s->argv)[a],*q=(char*)b;for(U i=0;i<=n;i++)q[i]=p[i];s->error=0;return n;}
R(file_open){
    UNUSED;if(!a||b>3){invalid(s);return 0;}I flags=0;static const I modes[]={0,577,1089,193};flags=modes[b];I fd;
#ifdef ARM_MACOS
    I mac=0x1000000|(flags&3);if(flags&64)mac|=0x200;if(flags&128)mac|=0x800;if(flags&512)mac|=0x400;if(flags&1024)mac|=8;fd=result(os_open((char*)a,mac,0666));
#else
    fd=sys(56,-100,a,(U)flags|0x80000,0666,0,0);
#endif
    if(fd<0){io(s,fd);return 0;}U*p=(U*)ar_alloc(8,0,0,s);*p=(U)fd;s->error=0;return (U)p;
}
R(file_close){UNUSED;if(!a||*(I*)a==-1){s->error=0;return 0;}I fd=*(I*)a;*(I*)a=-1;
#ifdef ARM_MACOS
    return io(s,result(os_close(fd)));
#else
    return io(s,sys(57,(U)fd,0,0,0,0,0));
#endif
}
R(file_drop){UNUSED;U saved=s->error;if(a){if(*(I*)a!=-1)ar_file_close(a,0,0,s);ar_free(a,0,0,s);}s->error=saved;return 0;}
R(file_read){UNUSED;if(!a||*(I*)a==-1){s->error=9;return (U)-9;}if((!b&&c)||(I)c<0){s->error=22;return (U)-22;}if(c>0x7fffffff)c=0x7fffffff;I v;do{v=rd(*(I*)a,(void*)b,c);}while(v==-4);s->error=v<0?(U)-v:0;return (U)v;}
R(file_write){UNUSED;if(!a||*(I*)a==-1){s->error=9;return (U)-9;}if((!b&&c)||(I)c<0){s->error=22;return (U)-22;}U n=0;while(n<c){U count=c-n;if(count>0x7fffffff)count=0x7fffffff;I v=wr(*(I*)a,(char*)b+n,count);if(v==-4)continue;if(v<=0){s->error=v<0?(U)-v:5;return v<0?(U)v:(U)-5;}n+=(U)v;}s->error=0;return n;}
R(stdout_write){UNUSED;if(a!=1&&a!=2)return invalid(s);I fd=(I)a;return ar_file_write((U)&fd,b,c,s);}
R(file_sync){UNUSED;if(!a||*(I*)a==-1)return invalid(s);
#ifdef ARM_MACOS
    return io(s,result(os_fsync(*(I*)a)));
#else
    return io(s,sys(82,*(U*)a,0,0,0,0,0));
#endif
}
R(file_replace){UNUSED;if(!a||!b)return invalid(s);
#ifdef ARM_MACOS
    return io(s,result(os_rename((char*)a,(char*)b)));
#else
    return io(s,sys(38,-100,a,-100,b,0,0));
#endif
}
R(file_remove){UNUSED;if(!a)return invalid(s);
#ifdef ARM_MACOS
    return io(s,result(os_unlink((char*)a)));
#else
    return io(s,sys(35,-100,a,0,0,0,0));
#endif
}
