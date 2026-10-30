/* User templates are ASTs, never source-text replacements. Definition identities
 * bind type parameters; concrete TypeIds key the specialization cache. The queue
 * is exhausted before type checking, ownership analysis and either backend. */
#define MAX_GENERIC_INSTANCES 256
#define MAX_GENERIC_EXPANSION 64
static Vec function_instances,struct_instances;
static int type_resolution_depth,specialization_expansion;

static Function *find_generic_function(const char *name){
    for(int i=0;i<generic_functions.n;i++){Function *f=generic_functions.v[i];if(same(f->t->text,name))return f;}return NULL;
}
static Class *find_generic_class(const char *name){
    for(int i=0;i<generic_classes.n;i++){Class *c=generic_classes.v[i];if(same(c->t->text,name))return c;}return NULL;
}
static Type class_type(Class *c){
    if(!c->type_ref){c->type_ref=mem(sizeof(*c->type_ref));c->type_ref->definition=c->id;}
    return (Type){TY_OBJ,0,c->t->text,c->type_ref};
}
static bool same_arguments(Vec a,Vec b){
    if(a.n!=b.n)return false;
    for(int i=0;i<a.n;i++)if(type_identity(*(Type*)a.v[i])!=type_identity(*(Type*)b.v[i]))return false;return true;
}
static void type_arity(Token *where,const char *name,int expected,int actual){
    if(expected!=actual)error(where,"%s exige %d argumentos de tipo; recebidos %d",name,expected,actual);
}
static void specialization_budget(Token *where){
    if(function_instances.n+struct_instances.n>=MAX_GENERIC_INSTANCES)error(where,"limite de 256 especializações genéricas excedido");
}
static Node *clone_node(Node *n){
    if(!n)return NULL;Node *out=mem(sizeof(*out));*out=*n;
    out->a=clone_node(n->a);out->b=clone_node(n->b);out->c=clone_node(n->c);out->step=clone_node(n->step);
    out->items=(Vec){0};out->type_args=(Vec){0};
    for(int i=0;i<n->items.n;i++)push(&out->items,clone_node(n->items.v[i]));
    for(int i=0;i<n->type_args.n;i++)push(&out->type_args,type_copy(*(Type*)n->type_args.v[i]));
    return out;
}
static Type resolve_type(Type t,Vec parameters,Vec arguments,Token *where);
static Vec resolve_arguments(Vec input,Vec parameters,Vec arguments,Token *where){
    Vec out={0};for(int i=0;i<input.n;i++){
        Type t=resolve_type(*(Type*)input.v[i],parameters,arguments,where);
        push(&out,type_copy(t));
    }return out;
}
static Class *instantiate_class(Class *generic,Vec arguments,Token *where,Collection *intrinsic){
    type_arity(where,generic->t->text,generic->type_params.n,arguments.n);
    for(int i=0;i<arguments.n;i++)if(((Type*)arguments.v[i])->kind==TY_VOID)error(where,"argumento de tipo não pode ser void");
    if(intrinsic&&intrinsic->instance)return intrinsic->instance;
    if(!intrinsic)for(int i=0;i<struct_instances.n;i++){Class *c=struct_instances.v[i];if(c->generic->id==generic->id&&same_arguments(c->type_args,arguments))return c;}
    if(!intrinsic)specialization_budget(where);
    int expansion=intrinsic?0:specialization_expansion+1;
    if(expansion>MAX_GENERIC_EXPANSION)error(where,"limite de expansão de classes genéricas (64) excedido");
    Class *c=mem(sizeof(*c));c->record=generic->record;c->value=generic->value;c->tagged=generic->tagged;c->sealed=generic->sealed;c->closure=generic->closure;c->id=intrinsic?intrinsic->ref->definition:++next_definition;c->generic=generic;c->type_args=arguments;c->site=where;c->expansion=expansion;
    c->t=mem(sizeof(*c->t));*c->t=*generic->t;
    char symbol[64];snprintf(symbol,sizeof(symbol),"__assis_%s_%u",c->record?"struct":"class",c->id);c->t->text=intrinsic?intrinsic->name:copy(symbol,strlen(symbol));
    size_t size=strlen(generic->t->text)+3;
    for(int i=0;i<arguments.n;i++)size+=strlen(type_name(*(Type*)arguments.v[i]))+2;
    c->display=mem(size);strcpy(c->display,generic->t->text);strcat(c->display,"<");
    for(int i=0;i<arguments.n;i++){if(i)strcat(c->display,", ");strcat(c->display,type_name(*(Type*)arguments.v[i]));}strcat(c->display,">");
    /* Publish a nominal shell before fields, permitting finite recursive types. */
    if(intrinsic){intrinsic->instance=c;c->type_ref=intrinsic->ref;c->display=intrinsic->display;}else push(&struct_instances,c);
    push(&classes,c);(void)class_type(c);
    Token *previous_site=instantiation_site;const char *previous_name=instantiation_name;instantiation_site=where;instantiation_name=generic->t->text;
    int previous_expansion=specialization_expansion;specialization_expansion=expansion;
    c->base_name=generic->base_name;
    if(c->base_name)c->base_type=resolve_type(generic->base_type,generic->type_params,arguments,c->base_name);
    for(int i=0;i<generic->variants.n;i++){
        Variant *original=generic->variants.v[i],*v=mem(sizeof(*v));v->t=original->t;v->tag=original->tag;
        for(int j=0;j<original->fields.n;j++){Field *field=original->fields.v[j],*f=mem(sizeof(*f));*f=*field;f->owner=c;f->ty=resolve_type(f->ty,generic->type_params,arguments,f->t);push(&v->fields,f);}push(&c->variants,v);
    }
    for(int i=0;i<generic->own_fields.n;i++){
        Field *original=generic->own_fields.v[i],*f=mem(sizeof(*f));*f=*original;f->owner=c;
        f->ty=resolve_type(f->ty,generic->type_params,arguments,f->t);push(&c->own_fields,f);
    }
    for(int i=0;i<generic->own_methods.n;i++){
        Function *original=generic->own_methods.v[i],*f=mem(sizeof(*f));
        f->t=original->t;f->id=++next_definition;f->owner=c;f->generic=original;f->site=where;f->expansion=expansion;
        f->private=original->private;f->pure=original->pure;f->safe=original->safe;f->receiver_mode=original->receiver_mode;f->body=clone_node(original->body);
        f->result_mode=original->result_mode;f->result_from=original->result_from;
        if(intrinsic&&intrinsic->map&&intrinsic->key.kind==TY_STR&&same(f->t->text,"_hash"))f->body=clone_node(text_hash_ast);
        f->result=resolve_type(original->result,generic->type_params,arguments,f->t);
        for(int j=0;j<original->params.n;j++){
            Var *parameter=original->params.v[j],*v=mem(sizeof(*v));v->t=parameter->t;
            v->ownership=parameter->ownership;v->ty=resolve_type(parameter->ty,generic->type_params,arguments,v->t);push(&f->params,v);
        }
        push(&c->own_methods,f);push(&all_functions,f);
    }
    specialization_expansion=previous_expansion;instantiation_site=previous_site;instantiation_name=previous_name;
    return c;
}
static void prepare_collections(void){
    if(!collections.n)return;load_collection_templates();
    for(int i=0;i<collections.n;i++){
        Collection *c=collections.v[i];if(c->instance)continue;
        Vec arguments={0};push(&arguments,type_copy(c->key));if(c->map)push(&arguments,type_copy(c->value));
        (void)instantiate_class(c->map?map_ast:array_ast,arguments,c->site,c);
    }
}
static Type resolve_type(Type t,Vec parameters,Vec arguments,Token *where){
    if(++type_resolution_depth>MAX_GENERIC_EXPANSION)error(where,"limite de expansão de tipos genéricos (64) excedido");
    int depth=t.depth;t.depth=0;
    if(t.kind==TY_VAR){
        bool found=false;
        for(int i=0;i<parameters.n;i++){TypeParameter *p=parameters.v[i];if(p->id==t.ref->definition){t=*(Type*)arguments.v[i];found=true;break;}}
        if(!found)error(where,"parâmetro de tipo fora de seu escopo");
    }else if(t.kind==TY_APPLY){
        Token *origin=t.ref->origin;Vec concrete=resolve_arguments(t.ref->arguments,parameters,arguments,origin);
        if(same(t.name,"Array")||same(t.name,"HashMap")){
            bool map=same(t.name,"HashMap");type_arity(origin,t.name,map?2:1,concrete.n);
            t=collection_type(*(Type*)concrete.v[0],map?*(Type*)concrete.v[1]:type_void,map,origin);
        }else{
            Class *generic=find_generic_class(t.name);
            if(!generic){if(find_class(t.name))error(origin,"tipo não genérico não aceita argumentos de tipo: %s",t.name);error(origin,"tipo genérico desconhecido: %s",t.name);}
            t=class_type(instantiate_class(generic,concrete,origin,NULL));
        }
    }else if(t.kind==TY_OBJ&&(!t.ref||!t.ref->definition)){
        Class *c=find_class(t.name);
        if(!c){if(find_generic_class(t.name))error(where,"tipo genérico exige argumentos de tipo: %s<...>",t.name);error(where,"tipo desconhecido: %s",t.name);}
        t=class_type(c);
    }else if(t.kind==TY_SLICE){
        TypeRef *ref=mem(sizeof(*ref));ref->origin=t.ref->origin;ref->arguments=resolve_arguments(t.ref->arguments,parameters,arguments,where);t.ref=ref;
    }else if(t.kind==TY_FN){
        TypeRef *ref=mem(sizeof(*ref));ref->origin=t.ref->origin;ref->pure=t.ref->pure;
        ref->modes=t.ref->modes;ref->safe=t.ref->safe;ref->closure=t.ref->closure;ref->receiver_mode=t.ref->receiver_mode;ref->result_mode=t.ref->result_mode;ref->result_from=t.ref->result_from;
        ref->arguments=resolve_arguments(t.ref->arguments,parameters,arguments,where);
        ref->result=type_copy(resolve_type(*t.ref->result,parameters,arguments,where));t.ref=ref;
    }
    t.depth+=depth;if(t.depth>64)error(where,"ponteiro aninhado demais após especialização");
    (void)type_identity(t);type_resolution_depth--;return t;
}
static Function *instantiate_function(Function *generic,Vec arguments,Token *where,Function *parent){
    type_arity(where,generic->t->text,generic->type_params.n,arguments.n);
    for(int i=0;i<arguments.n;i++)if(((Type*)arguments.v[i])->kind==TY_VOID)error(where,"argumento de tipo não pode ser void");
    for(int i=0;i<function_instances.n;i++){Function *f=function_instances.v[i];if(f->generic->id==generic->id&&same_arguments(f->type_args,arguments))return f;}
    specialization_budget(where);
    int expansion=parent->expansion+1;
    if(expansion>MAX_GENERIC_EXPANSION)error(where,"limite de expansão de funções genéricas (64) excedido");
    Function *f=mem(sizeof(*f));f->t=generic->t;f->id=++next_definition;f->generic=generic;f->type_args=arguments;
    f->pure=generic->pure;f->safe=generic->safe;f->site=where;f->expansion=expansion;f->body=clone_node(generic->body);
    f->result_mode=generic->result_mode;f->result_from=generic->result_from;
    Token *previous_site=instantiation_site;const char *previous_name=instantiation_name;instantiation_site=where;instantiation_name=generic->t->text;
    f->result=resolve_type(generic->result,generic->type_params,arguments,generic->t);
    for(int i=0;i<generic->params.n;i++){
        Var *original=generic->params.v[i],*v=mem(sizeof(*v));v->t=original->t;
        v->ownership=original->ownership;v->ty=resolve_type(original->ty,generic->type_params,arguments,v->t);push(&f->params,v);
    }
    push(&function_instances,f);push(&all_functions,f);instantiation_site=previous_site;instantiation_name=previous_name;return f;
}
static void resolve_node(Node *n,Function *f){
    if(!n)return;Vec parameters=f->generic?f->generic->type_params:(Vec){0};
    Vec arguments=f->type_args;
    if(f->owner&&f->owner->generic){parameters=f->owner->generic->type_params;arguments=f->owner->type_args;}
    if(n->kind==N_NEW&&n->decl.kind==TY_OBJ&&!n->decl.ref&&!find_class(n->decl.name)&&!find_generic_class(n->decl.name))error(n->t,"classe inexistente para new: %s",n->decl.name);
    if(n->kind==N_LET||n->kind==N_NEW||n->kind==N_IS||n->kind==N_CAST||(n->kind==N_BUILTIN&&(n->op==T_BUFFER||n->op==T_TRY_BUFFER)))n->decl=resolve_type(n->decl,parameters,arguments,n->t);
    if(n->kind==N_NAME&&n->specialized){
        Function *generic=find_generic_function(n->t->text);
        if(!generic){if(find_fn(n->t->text))error(n->t,"função não genérica não aceita argumentos de tipo");error(n->t,"função genérica desconhecida: %s",n->t->text);}
        Vec concrete=resolve_arguments(n->type_args,parameters,arguments,n->t);
        n->fn=instantiate_function(generic,concrete,n->t,f);
    }
    resolve_node(n->a,f);resolve_node(n->b,f);resolve_node(n->c,f);resolve_node(n->step,f);
    for(int i=0;i<n->items.n;i++)resolve_node(n->items.v[i],f);
}
/* Symbolic effect checking also runs for unused pure templates. Track lexical
 * bindings so a callback never inherits a global function's effect by spelling.
 * Operations dependent on T still receive full checking on each instance. */
static Vec template_bindings;
static Type substitute_symbolic(Type t,Vec parameters,Vec arguments){
    if(t.kind==TY_VAR){
        for(int i=0;i<parameters.n&&i<arguments.n;i++)if(((TypeParameter*)parameters.v[i])->id==t.ref->definition){Type out=*(Type*)arguments.v[i];out.depth+=t.depth;return out;}
    }else if(t.kind==TY_FN||t.kind==TY_APPLY||t.kind==TY_SLICE){
        TypeRef *ref=mem(sizeof(*ref));*ref=*t.ref;ref->arguments=(Vec){0};
        for(int i=0;i<t.ref->arguments.n;i++)push(&ref->arguments,type_copy(substitute_symbolic(*(Type*)t.ref->arguments.v[i],parameters,arguments)));
        if(t.kind==TY_FN)ref->result=type_copy(substitute_symbolic(*t.ref->result,parameters,arguments));t.ref=ref;
    }
    return t;
}
static Type template_expression_type(Node *n){
    if(!n)return type_void;
    if(n->kind==N_NEW)return n->decl;
    if(n->kind==N_INT)return n->t->kind==T_REAL?(Type){TY_F64,0,NULL,NULL}:type_i64;
    if(n->kind==N_BOOL)return type_bool;
    if(n->kind==N_NAME){
        for(int i=template_bindings.n-1;i>=0;i--){Var *v=template_bindings.v[i];if(same(v->t->text,n->t->text))return v->ty;}
        Function *f=find_fn(n->t->text);if(!f)f=find_generic_function(n->t->text);
        if(f)return n->specialized?substitute_symbolic(function_type(f),f->type_params,n->type_args):function_type(f);
    }else if(n->kind==N_CALL){
        Type callee=template_expression_type(n->a);if(function_value(callee))return *callee.ref->result;
    }else if(n->kind==N_MEMBER){
        Type parent=template_expression_type(n->a);Class *c=parent.kind==TY_APPLY?find_generic_class(parent.name):find_class(parent.name);
        if(c)for(int i=0;i<c->own_fields.n;i++){Field *field=c->own_fields.v[i];if(same(field->t->text,n->t->text))return parent.kind==TY_APPLY?substitute_symbolic(field->ty,c->type_params,parent.ref->arguments):field->ty;}
    }
    return type_void;
}
static void check_template_purity(Node *n){
    if(!n)return;
    if(n->kind==N_MATCH){
        check_template_purity(n->a);Type subject=template_expression_type(n->a);Class *c=subject.kind==TY_APPLY?find_generic_class(subject.name):find_class(subject.name);
        for(int i=0;i<n->items.n;i++){
            Node *arm=n->items.v[i];int old=template_bindings.n;Variant *variant=NULL;
            if(c)for(int j=0;j<c->variants.n;j++)if(same(((Variant*)c->variants.v[j])->t->text,arm->t->text))variant=c->variants.v[j];
            for(int j=0;j<arm->items.n;j++){Node *binding=arm->items.v[j];Var *v=mem(sizeof(*v));v->t=binding->t;v->ty=variant&&j<variant->fields.n?((Field*)variant->fields.v[j])->ty:type_i64;if(c&&subject.kind==TY_APPLY)v->ty=substitute_symbolic(v->ty,c->type_params,subject.ref->arguments);push(&template_bindings,v);}
            check_template_purity(arm->a);template_bindings.n=old;
        }
        return;
    }
    if(n->kind==N_BLOCK){
        int old=template_bindings.n;
        for(int i=0;i<n->items.n;i++)check_template_purity(n->items.v[i]);
        template_bindings.n=old;return;
    }
    if(n->kind==N_PRINT||n->kind==N_FREE||n->kind==N_DEFER||(n->kind==N_NEW&&(n->op==T_TRY_NEW||!declared_value_type(n->decl)))||n->kind==N_ARRAY||n->kind==N_STR||n->kind==N_NULL||n->kind==N_SELF||n->kind==N_INDEX||n->kind==N_UNSAFE)
        error(n->t,"efeito ou referência não permitido em template pure");
    if(n->kind==N_UNARY&&(n->op=='&'||n->op=='*'))error(n->t,"pure não permite ponteiros");
    if(n->kind==N_BUILTIN&&n->op!=T_I64&&n->op!=T_U8&&n->op!=T_NUMTYPE&&n->op!=T_BOOL)error(n->t,"efeito não permitido em template pure");
    if(n->kind==N_LET){
        if(n->ownership||!pure_contract(n->decl,true))error(n->t,"local pure exige valor escalar ou função pure sem own/borrow");
        check_template_purity(n->a);Var *v=mem(sizeof(*v));v->t=n->t;v->ty=n->decl;push(&template_bindings,v);return;
    }
    if(n->kind==N_CALL){
        Type callee=template_expression_type(n->a);
        if(!function_value(callee)||!callee.ref->pure)error(n->t,"template pure exige chamada de função pure com contrato explícito");
    }
    if(n->kind==N_NAME){
        Type value=template_expression_type(n);
        if(function_value(value)&&!pure_contract(value,true))error(n->t,"pure não permite função com efeitos: %s",n->t->text);
    }
    check_template_purity(n->a);check_template_purity(n->b);check_template_purity(n->c);check_template_purity(n->step);
    for(int i=0;i<n->items.n;i++)check_template_purity(n->items.v[i]);
}
static void prepare_generics(void){
    /* Module names were bound to declarations before this pass. Generated
     * symbols are backend names only; cache keys remain definition identities. */
    Vec definitions={0};
    for(int i=0;i<classes.n;i++)push(&definitions,((Class*)classes.v[i])->t);
    for(int i=0;i<generic_classes.n;i++)push(&definitions,((Class*)generic_classes.v[i])->t);
    for(int i=0;i<functions.n;i++)push(&definitions,((Function*)functions.v[i])->t);
    for(int i=0;i<generic_functions.n;i++)push(&definitions,((Function*)generic_functions.v[i])->t);
    int class_count=classes.n+generic_classes.n;
    for(int i=0;i<definitions.n;i++)for(int j=0;j<i;j++)if(same(((Token*)definitions.v[i])->text,((Token*)definitions.v[j])->text))
        error(definitions.v[i],i<class_count?"classe declarada duas vezes":j>=class_count?"função declarada duas vezes":"nome principal declarado duas vezes");
    for(int i=0;i<generic_functions.n;i++){
        Function *f=generic_functions.v[i];
        if(same(f->t->text,ENTRY)||same(f->t->text,"main"))error(f->t,"main/main não pode ser genérica");
        for(int j=0;j<f->params.n;j++)for(int k=0;k<j;k++)if(same(((Var*)f->params.v[j])->t->text,((Var*)f->params.v[k])->t->text))error(((Var*)f->params.v[j])->t,"parâmetro declarado duas vezes");
        if(f->pure){
            if(!pure_contract(f->result,true))error(f->t,"pure exige retorno escalar ou função pure após especialização");
            template_bindings.n=0;
            for(int j=0;j<f->params.n;j++){Var *v=f->params.v[j];if(!pure_contract(v->ty,true))error(v->t,"parâmetro pure exige escalar ou função pure após especialização");push(&template_bindings,v);}
            check_template_purity(f->body);
        }
    }
    int class_cursor=0,function_cursor=0;
    do{
        while(class_cursor<classes.n){Class *c=classes.v[class_cursor++];
            instantiation_site=c->site;instantiation_name=c->generic?c->generic->t->text:NULL;specialization_expansion=c->expansion;
            if(c->base_name){
                if(c->base_type.kind==TY_OBJ&&!find_class(c->base_type.name)&&!find_generic_class(c->base_type.name))error(c->base_name,"classe base desconhecida");
                c->base_type=resolve_type(c->base_type,(Vec){0},(Vec){0},c->base_name);c->base=find_class(c->base_type.name);
            }
            for(int j=0;j<c->own_fields.n;j++){Field *field=c->own_fields.v[j];field->ty=resolve_type(field->ty,(Vec){0},(Vec){0},field->t);}
            for(int j=0;j<c->variants.n;j++){Variant *v=c->variants.v[j];for(int k=0;k<v->fields.n;k++){Field *field=v->fields.v[k];field->ty=resolve_type(field->ty,(Vec){0},(Vec){0},field->t);}}
        }
        while(function_cursor<all_functions.n){Function *f=all_functions.v[function_cursor++];
            instantiation_site=f->site;instantiation_name=f->generic?f->generic->t->text:NULL;specialization_expansion=f->expansion;
            f->result=resolve_type(f->result,(Vec){0},(Vec){0},f->t);
            for(int j=0;j<f->params.n;j++){Var *v=f->params.v[j];v->ty=resolve_type(v->ty,(Vec){0},(Vec){0},v->t);}
            resolve_node(f->body,f);
        }
        instantiation_site=NULL;specialization_expansion=0;prepare_collections();
    }while(class_cursor<classes.n||function_cursor<all_functions.n);
    for(int i=0;i<all_functions.n;i++){Function *f=all_functions.v[i];instantiation_site=f->site;instantiation_name=f->generic?f->generic->t->text:NULL;signature(f);}
    instantiation_site=NULL;
}
