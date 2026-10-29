/* Independent C ABI oracle. Exported functions deliberately mix register
 * classes, exhausted register banks, narrow values and reverse calls. */
#include <stdint.h>
#include <stddef.h>
#ifdef _WIN32
#define API __declspec(dllexport)
#else
#define API __attribute__((visibility("default")))
#endif
API int64_t ffi_mix(int64_t a,double b,int32_t c,float d,int64_t e,int64_t f,int64_t g,double h,int64_t i,int64_t j){
    return a+2*(int64_t)b+3*c+4*(int64_t)d+5*e+6*f+7*g+8*(int64_t)h+9*i+10*j;
}
API double ffi_reals(double a,double b,double c,double d,double e,double f,double g,double h,double i,double j){return a+2*b+3*c+4*d+5*e+6*f+7*g+8*h+9*i+10*j;}
API int8_t ffi_narrow(int8_t a,uint8_t b,int16_t c,uint16_t d,int32_t e,uint32_t f){return (int8_t)(a+b+c+d+e+f);}
API void ffi_bytes(uint8_t *buffer,int64_t n){for(int64_t i=0;i<n;i++)buffer[i]=(uint8_t)(i+65);}
API int64_t ffi_callback(uintptr_t address){
    typedef int64_t (*callback)(int64_t,double,int32_t,float,int64_t,int64_t,int64_t,double,int64_t,int64_t);
    return ((callback)address)(1,2.0,3,4.0f,5,6,7,8.0,9,10);
}
API double ffi_real_callback(uintptr_t address){typedef double (*callback)(double,double,double,double,double,double,double,double,double,double);return ((callback)address)(1,2,3,4,5,6,7,8,9,10);}
API int64_t ffi_twice(uintptr_t address,int64_t n){typedef int64_t (*callback)(int64_t);callback cb=(callback)address;return cb(n)+cb(n+1);}
static int64_t live_handles,closed_handles;
API int64_t ffi_open_handle(void){return ++live_handles;}
API void ffi_close_handle(int64_t handle){if(handle>0){live_handles--;closed_handles++;}}
API int64_t ffi_live_handles(void){return live_handles;}
API int64_t ffi_closed_handles(void){return closed_handles;}
/* Force a nonvolatile register to hold a value while the callback is active. */
API int64_t ffi_runtime_register(uintptr_t address,int64_t n){
#if defined(__aarch64__) || defined(__arm64__)
    register uintptr_t marker __asm__("x27")=UINT64_C(0x123456789abcdef0);
#else
    register uintptr_t marker __asm__("r15")=UINT64_C(0x123456789abcdef0);
#endif
    __asm__ volatile("" : "+r"(marker));
    int64_t result=((int64_t (*)(int64_t))address)(n);
    __asm__ volatile("" : "+r"(marker));
    return marker==UINT64_C(0x123456789abcdef0)?result:-1;
}
