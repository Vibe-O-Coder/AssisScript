/* Typed scalar values, independent of AST ownership and layout. Each operand
 * precedes its consumer; &&/|| retain lazy evaluation at the emission boundary.
 * Resource expressions are lowered by backend_ir.h; --no-opt is the separate
 * checked AST reference backend. */
enum { IV_CONSTANT,IV_LOCAL,IV_UNARY,IV_BINARY,IV_CAST,IV_CALL };
struct IRExpr {int id,kind,op;Type type;Token *site;unsigned effects;uint64_t value;Var *local;Function *callee;IRExpr *a,*b;Vec arguments;};
static Vec ir_values;
static bool ir_scalar(Type type){return !type.depth&&(integer(type)||floating(type)||equal_type(type,type_bool));}
static IRExpr *ir_expression(Node *n){
    if(!n||!ir_scalar(n->ty)||n->temp)return NULL;
    IRExpr value={0};value.type=n->ty;value.site=n->t;value.op=n->op;
    uint64_t folded;
    if(constant(n,&folded)){value.kind=IV_CONSTANT;value.value=folded;}
    else if(n->kind==N_INT||n->kind==N_BOOL){value.kind=IV_CONSTANT;value.value=n->kind==N_INT?n->t->number:(uint64_t)(n->t->kind==T_TRUE);}
    else if(n->kind==N_NAME&&n->var){value.kind=IV_LOCAL;value.local=n->var;value.effects=IR_READ;}
    else if(n->kind==N_UNARY&&(n->op=='+'||n->op=='-'||n->op=='~'||n->op=='!')&&n->a->ir){value.kind=IV_UNARY;value.a=n->a->ir;value.effects=value.a->effects;}
    else if(n->kind==N_BINARY&&n->a->ir&&n->b->ir){
        value.kind=IV_BINARY;value.a=n->a->ir;value.b=n->b->ir;value.effects=value.a->effects|value.b->effects;
        if(n->op=='/'||n->op=='%'||n->op==T_SHL||n->op==T_SHR)value.effects|=IR_TRAP;
    }
    else if(n->kind==N_BUILTIN&&n->items.n==1&&(n->op==T_I64||n->op==T_U8||n->op==T_NUMTYPE||n->op==T_BOOL)&&((Node*)n->items.v[0])->ir){
        value.kind=IV_CAST;value.a=((Node*)n->items.v[0])->ir;value.effects=value.a->effects;
        if(floating(value.a->type)&&integer(value.type))value.effects|=IR_TRAP;
    }
    else if(n->kind==N_CALL&&n->fn&&!n->fn->owner&&!n->fn->foreign){
        value.kind=IV_CALL;value.callee=n->fn;value.effects=IR_CALL|IR_TRAP;
        if(!n->fn->pure)value.effects|=IR_READ|IR_WRITE|IR_ALLOC|IR_IO;
        for(int i=0;i<n->items.n;i++){Node *arg=n->items.v[i];if(!arg->ir)return NULL;push(&value.arguments,arg->ir);value.effects|=arg->ir->effects;}
    }
    else return NULL;
    IRExpr *out=mem(sizeof(*out));*out=value;out->id=ir_values.n;push(&ir_values,out);return out;
}
static void ir_expressions(Node *n){
    if(!n)return;
    ir_expressions(n->a);ir_expressions(n->b);ir_expressions(n->c);ir_expressions(n->step);
    for(int i=0;i<n->items.n;i++)ir_expressions(n->items.v[i]);
    n->ir=ir_expression(n);
}
static const char *ir_value_kind(int kind){
    switch(kind){case IV_CONSTANT:return "constant";case IV_LOCAL:return "local";case IV_UNARY:return "unary";case IV_BINARY:return "binary";case IV_CAST:return "cast";case IV_CALL:return "call";default:fatal("opcode de valor IR inválido");}return "";
}
static void ir_print_values(void){
    fputs(",\"valueFormat\":\"AssisScript-ScalarIR-v1\",\"values\":[",stdout);
    for(int i=0;i<ir_values.n;i++){
        IRExpr *v=ir_values.v[i];if(i)fputc(',',stdout);fprintf(stdout,"{\"id\":%d,\"opcode\":",v->id);json_string(stdout,ir_value_kind(v->kind));
        fputs(",\"type\":",stdout);json_string(stdout,type_name(v->type));fprintf(stdout,",\"line\":%d,\"effects\":%u,\"operator\":%d,\"inputs\":[",v->site->line,v->effects,v->op);
        if(v->a)fprintf(stdout,"%d",v->a->id);if(v->b)fprintf(stdout,",%d",v->b->id);
        for(int j=0;j<v->arguments.n;j++){if(j)fputc(',',stdout);fprintf(stdout,"%d",((IRExpr*)v->arguments.v[j])->id);}fputc(']',stdout);
        if(v->kind==IV_CONSTANT)fprintf(stdout,",\"bits\":\"%016llx\"",(unsigned long long)v->value);
        if(v->local){fputs(",\"local\":",stdout);json_string(stdout,v->local->t->text);}
        if(v->callee){fputs(",\"callee\":",stdout);json_string(stdout,v->callee->t->text);}fputc('}',stdout);
    }fputc(']',stdout);
}
