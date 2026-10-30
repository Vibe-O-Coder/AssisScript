/* Safe is the default entry profile. Legacy functions can only be reached from
 * checked code through an explicit unsafe block; --legacy opts out at the root.
 * External C text never crosses a checked signature: use managed UTF-8/slices. */
static Vec safe_visiting;
static void safe_resource(Type t,Token *where){
    if(closure_type(t))return;
    if(slice_type(t))return;
    if(equal_type(t,type_str))error(where,"safe ainda não aceita text de vida externa; use unsafe na fronteira");
    owned_type(t,where);if(t.depth)return;
    if(equal_type(t,type_file))return;
    Collection *c=collection_of(t);
    if(c){if(equal_type(c->key,type_str)||(c->map&&equal_type(c->value,type_str)))error(where,"safe exige coleções sem text de vida externa");return;}
    Class *cls=find_class(t.name);
    for(int i=0;i<safe_visiting.n;i++)if(safe_visiting.v[i]==cls)return;
    if(safe_visiting.n>=256)error(where,"limite de 256 níveis de recursos safe excedido");push(&safe_visiting,cls);
    for(int i=0;i<cls->fields.n;i++){Field *f=cls->fields.v[i];if(resource_type(f->ty)){if(!f->owned&&!(cls->closure&&f->borrowed))error(where,"safe exige campos de referência own");safe_resource(f->ty,f->t);}}
    for(int i=0;i<cls->variants.n;i++){Variant *v=cls->variants.v[i];for(int j=0;j<v->fields.n;j++){Field *f=v->fields.v[j];if(f->owned)safe_resource(f->ty,f->t);}}
    safe_visiting.n--;
}
static void safe_signature(TypeRef *r,Token *t){
    for(int i=0;i<r->arguments.n;i++){Type p=*(Type*)r->arguments.v[i];if(resource_type(p)){if(!parameter_mode(r,i))error(t,"safe exige own/borrow na assinatura");safe_resource(p,t);}}
    if(resource_type(*r->result)){if(!r->result_mode)error(t,"safe exige own/borrow no retorno");safe_resource(*r->result,t);}
}
static void safe_node(Node *n){
    if(!n)return;if(n->kind==N_UNSAFE)return;
    if(n->kind==N_LET&&resource_type(n->decl)){
        if(equal_type(n->decl,type_str)&&n->immutable&&n->a->kind==N_STR)n->var->static_text=true;
        else{if(!n->ownership)error(n->t,"safe exige own/borrow; operação legada exige unsafe { ... }");safe_resource(n->decl,n->t);}
    }
    if(n->kind==N_NAME&&n->var&&resource_type(n->ty)&&!n->var->ownership&&!n->var->static_text)error(n->t,"referência legada em safe exige unsafe { ... }");
    if((n->kind==N_SELF&&!n->ownership)||(n->kind==N_UNARY&&(n->op=='&'||n->op=='*'))||(n->kind==N_BINARY&&n->ty.depth)||n->kind==N_DEFER)error(n->t,"operação bruta em safe exige unsafe { ... }");
    if(n->kind==N_CALL){
        if(n->fn&&n->fn->owner){
            if((!collection_of(n->a->a->ty)&&!n->fn->receiver_mode)||!n->a->a->ownership)error(n->t,"método legado em safe exige unsafe { ... }");safe_resource(n->a->a->ty,n->t);
        }else{TypeRef *r=call_contract(n);if(!r->safe)error(n->t,"chamada legada em safe exige unsafe { ... }");safe_signature(r,n->t);}
    }
    if((n->kind==N_NEW&&!value_type(n->ty))||n->kind==N_ARRAY){if(!n->ownership)error(n->t,"alocação em safe exige destino own ou unsafe { ... }");safe_resource(n->cls&&n->cls->closure?class_type(n->cls):n->ty,n->t);}
    if(n->kind==N_BUILTIN){
        if(n->op==T_C_CALLBACK)error(n->t,"c_callback exige unsafe { ... }");
        if(n->op==T_TEXT||n->op==T_BYTES)error(n->t,"conversão de text externo em safe exige unsafe { ... }");
        if((n->op==T_BUFFER||n->op==T_TRY_BUFFER||n->op==T_ALLOC)&&!n->ownership)error(n->t,"alocação em safe exige destino own");
        if(n->op==T_READ&&!((Node*)n->items.v[0])->ownership)error(n->t,"buffer legado em safe exige unsafe { ... }");
        if((n->op==T_FILE_READ||n->op==T_FILE_WRITE||n->op==T_ARG_COPY||n->op==T_WRITE_BYTES)&&!((Node*)n->items.v[1])->ownership)error(n->t,"buffer legado em safe exige unsafe { ... }");
    }
    if(n->kind==N_INDEX&&n->a->ty.depth&&!n->a->ownership)error(n->t,"indexação bruta em safe exige unsafe { ... }");
    if(n->kind==N_FREE&&!n->var&&!(n->a->kind==N_CALL&&n->a->ownership==1))error(n->t,"free legado em safe exige unsafe { ... }");
    safe_node(n->a);safe_node(n->b);safe_node(n->c);safe_node(n->step);
    for(int i=0;i<n->items.n;i++)safe_node(n->items.v[i]);
}
static void check_safety(void){
    if(safe_entry&&main_function&&!main_function->safe&&!main_function->pure)error(main_function->t,"--safe exige entrada declarada safe fn (padrão); migre para safe fn main ou use --legacy explicitamente");
    for(int i=0;i<all_functions.n;i++){
        Function *f=all_functions.v[i];if(!f->safe)continue;
        instantiation_site=f->site;instantiation_name=f->generic?f->generic->t->text:NULL;
        if(f->owner&&f->owner->closure)safe_resource(class_type(f->owner),f->t);
        safe_signature(function_type(f).ref,f->t);safe_node(f->body);
    }
    instantiation_site=NULL;
}
