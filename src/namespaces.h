/* Module names bind AST identities before generic specialization. */
typedef struct {Token *token;char *local,*qualified;bool exported,type;} ModuleSymbol;
static Vec module_symbols;
/* Platform branches contain declarations, without nested platform/namespace. */
static void scan_platforms(void){
    Vec out={0};int depth=0;
    for(int i=0;i<tokens.n;i++){
        Token *t=tokens.v[i];
        if(t->kind==T_PLATFORM){
            if(depth)error(t,"platform só aceita declarações no nível do módulo");
            if(i+4>=tokens.n||((Token*)tokens.v[i+1])->kind!='('||((Token*)tokens.v[i+2])->kind!=T_STR||((Token*)tokens.v[i+3])->kind!=')'||((Token*)tokens.v[i+4])->kind!='{')error(t,"use platform(\"linux-x64\") { declarações }");
            Token *name=tokens.v[i+2];if(strlen(name->str)!=name->len||(!same(name->str,"linux-x64")&&!same(name->str,"windows-x64")&&!same(name->str,"macos-x64")&&!same(name->str,"linux-arm64")&&!same(name->str,"macos-arm64")&&!same(name->str,"linux")&&!same(name->str,"macos")))error(name,"plataforma desconhecida");
            bool enabled=same(name->str,target_windows?"windows-x64":target_macos?(target_arm64?"macos-arm64":"macos-x64"):(target_arm64?"linux-arm64":"linux-x64"))||(!target_windows&&same(name->str,target_macos?"macos":"linux"));int level=1,j=i+5;
            for(;j<tokens.n;j++){
                Token *p=tokens.v[j];if(p->kind==T_FILE_END||p->kind==T_EOF||p->file!=t->file)error(t,"platform exige bloco fechado no mesmo arquivo");
                if(p->kind==T_PLATFORM||p->kind==T_NAMESPACE)error(p,"platform não aceita platform/namespace aninhado");
                if(p->kind=='{')level++;if(p->kind=='}'){level--;if(!level)break;}
                if(enabled)push(&out,p);
            }
            if(level)error(t,"platform exige }");i=j;continue;
        }
        if(t->kind=='{')depth++;if(t->kind=='}')depth--;push(&out,t);
    }tokens=out;
}
static char *qualified_name(const char *space,const char *name){size_t size=strlen(space)+strlen(name)+3;char *out=mem(size);snprintf(out,size,"%s::%s",space,name);return out;}
static Token *qualified_token(Token *t){
    Token *out=t;
    while(peek()->kind==':'&&cursor+1<tokens.n&&((Token*)tokens.v[cursor+1])->kind==':'&&cursor+2<tokens.n&&((Token*)tokens.v[cursor+2])->kind==T_ID){
        take();take();Token *next=take();out=mem(sizeof(*out));*out=*t;out->text=qualified_name(t->text,next->text);t=out;
    }
    return out;
}
static void scan_namespaces(void){
    Vec filtered={0};int depth=0,parens=0;bool exported=false,header=false;
    for(int i=0;i<tokens.n;i++){
        Token *t=tokens.v[i];
        if(!depth&&!header&&t->kind==T_NAMESPACE){
            if(exported)error(t,"public deve preceder uma declaração");
            if(t->file->space)error(t,"namespace declarado duas vezes no módulo");
            for(int j=0;j<module_symbols.n;j++)if(((ModuleSymbol*)module_symbols.v[j])->token->file==t->file)error(t,"namespace deve preceder declarações");
            Token *name=tokens.v[++i];if(name->kind!=T_ID)error(name,"namespace exige identificador");
            t->file->space=name->text;Token *end=tokens.v[++i];if(end->kind!=';')error(end,"namespace exige ;");continue;
        }
        if(!depth&&!header&&t->kind==T_PUBLIC){if(exported)error(t,"public duplicado");exported=true;continue;}
        bool type=t->kind==T_CLASS||t->kind==T_STRUCT||t->kind==T_ENUM;
        if(!depth&&!parens&&!header&&(type||t->kind==T_FN||t->kind==T_CONST)){
            Token *name=tokens.v[i+1];if(name->kind!=T_ID)error(name,"declaração exige nome");
            if(exported&&!name->file->space)error(name,"public exige namespace no módulo");
            ModuleSymbol *symbol=mem(sizeof(*symbol));symbol->token=name;symbol->local=name->text;symbol->type=type;
            symbol->exported=exported||!name->file->space;symbol->qualified=name->file->space?qualified_name(name->file->space,name->text):name->text;
            if(name->file->space&&(same(symbol->local,ENTRY)||same(symbol->local,"main")))error(name,"entrada main/assis_assis deve ficar no módulo sem namespace");
            name->text=symbol->qualified;push(&module_symbols,symbol);exported=false;header=true;
        }
        if(t->kind==T_FILE_END||t->kind==T_EOF){if(exported)error(t,"public sem declaração");}
        push(&filtered,t);if(t->kind=='{'){depth++;header=false;}if(t->kind=='}')depth--;if(t->kind=='(')parens++;if(t->kind==')')parens--;if(!depth&&t->kind==';')header=false;
    }
    tokens=filtered;
}
static char *module_name(const char *name,Token *where,bool type){
    ModuleSymbol *found=NULL;
    if(!strstr(name,"::")&&where->file->space){
        char *local=qualified_name(where->file->space,name);
        for(int i=0;i<module_symbols.n;i++){ModuleSymbol *s=module_symbols.v[i];if(s->type==type&&same(s->qualified,local)){found=s;break;}}
        free(local);
    }
    if(!found)for(int i=0;i<module_symbols.n;i++){ModuleSymbol *s=module_symbols.v[i];if(s->type==type&&same(s->qualified,name)){found=s;break;}}
    if(!found)return (char*)name;
    if(!found->exported&&found->token->file!=where->file)error(where,"símbolo privado do módulo: %s",found->qualified);
    return found->qualified;
}
static Type module_type(Type t,Token *where){
    if(t.kind==TY_OBJ||t.kind==TY_APPLY)t.name=module_name(t.name,t.ref&&t.ref->origin?t.ref->origin:where,true);
    if(t.kind==TY_APPLY||t.kind==TY_FN||t.kind==TY_SLICE){
        for(int i=0;i<t.ref->arguments.n;i++)*(Type*)t.ref->arguments.v[i]=module_type(*(Type*)t.ref->arguments.v[i],where);
        if(t.kind==TY_FN)*t.ref->result=module_type(*t.ref->result,where);
    }
    return t;
}
static Vec module_bindings;
static void module_node(Node *n){
    if(!n)return;
    int old=module_bindings.n;
    if(n->kind==N_BLOCK){for(int i=0;i<n->items.n;i++)module_node(n->items.v[i]);module_bindings.n=old;return;}
    if(n->kind==N_ARM){for(int i=0;i<n->items.n;i++)push(&module_bindings,((Node*)n->items.v[i])->t->text);module_node(n->a);module_bindings.n=old;return;}
    if(n->kind==N_NAME){
        bool local=false;for(int i=module_bindings.n-1;i>=0;i--)if(same(module_bindings.v[i],n->t->text)){local=true;break;}
        if(!local){Token *t=mem(sizeof(*t));*t=*n->t;t->text=module_name(t->text,t,false);n->t=t;}
    }
    if(n->kind==N_LET||n->kind==N_NEW||n->kind==N_IS||n->kind==N_CAST||(n->kind==N_BUILTIN&&n->op==T_BUFFER))n->decl=module_type(n->decl,n->t);
    for(int i=0;i<n->type_args.n;i++)*(Type*)n->type_args.v[i]=module_type(*(Type*)n->type_args.v[i],n->t);
    module_node(n->a);module_node(n->b);module_node(n->c);module_node(n->step);
    for(int i=0;i<n->items.n;i++)module_node(n->items.v[i]);
    if(n->kind==N_LET)push(&module_bindings,n->t->text);
}
static void bind_namespaces(void){
    for(int i=0;i<global_constants.n;i++){GlobalConstant *g=global_constants.v[i];module_bindings.n=0;g->ty=module_type(g->ty,g->t);module_node(g->value);}
    Vec class_groups[]={classes,generic_classes},function_groups[]={functions,generic_functions};
    for(int g=0;g<2;g++)for(int i=0;i<class_groups[g].n;i++){
        Class *c=class_groups[g].v[i];if(c->base_name)c->base_type=module_type(c->base_type,c->base_name);
        for(int j=0;j<c->own_fields.n;j++){Field *f=c->own_fields.v[j];f->ty=module_type(f->ty,f->t);}
        for(int j=0;j<c->variants.n;j++){Variant *v=c->variants.v[j];for(int k=0;k<v->fields.n;k++){Field *f=v->fields.v[k];f->ty=module_type(f->ty,f->t);}}
    }
    Vec all={0};for(int g=0;g<2;g++)for(int i=0;i<function_groups[g].n;i++)push(&all,function_groups[g].v[i]);
    for(int g=0;g<2;g++)for(int i=0;i<class_groups[g].n;i++){Class *c=class_groups[g].v[i];for(int j=0;j<c->own_methods.n;j++)push(&all,c->own_methods.v[j]);}
    for(int i=0;i<all.n;i++){
        Function *f=all.v[i];module_bindings.n=0;f->result=module_type(f->result,f->t);
        for(int j=0;j<f->params.n;j++){Var *v=f->params.v[j];v->ty=module_type(v->ty,v->t);push(&module_bindings,v->t->text);}
        module_node(f->body);
    }
}
