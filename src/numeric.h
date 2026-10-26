/* Scalar numeric representation. Values travel as bits in the internal ABI. */
static bool floating(Type t){return !t.depth&&(t.kind==TY_F32||t.kind==TY_F64);}
static bool integer(Type t){return !t.depth&&(t.kind==TY_I64||t.kind==TY_U8||(t.kind>=TY_I8&&t.kind<=TY_U64));}
static bool unsigned_integer(Type t){return !t.depth&&(t.kind==TY_U8||t.kind==TY_U16||t.kind==TY_U32||t.kind==TY_U64);}
static int scalar_bytes(Type t){
    if(t.depth)return 8;
    switch(t.kind){case TY_U8:case TY_I8:case TY_BOOL:return 1;case TY_I16:case TY_U16:return 2;case TY_I32:case TY_U32:case TY_F32:return 4;default:return 8;}
}
static Type numeric_type(const char *name){
    const char *names[]={"i8","i16","i32","u16","u32","u64","f32","f64"};
    for(int i=0;i<8;i++)if(same(name,names[i]))return (Type){(TypeKind)(TY_I8+i),0,NULL,NULL};
    return same(name,"u8")?type_u8:type_i64;
}
static const char *numeric_name(Type t){
    static const char *names[]={"i8","i16","i32","u16","u32","u64","f32","f64"};
    return t.kind>=TY_I8&&t.kind<=TY_F64?names[t.kind-TY_I8]:NULL;
}
