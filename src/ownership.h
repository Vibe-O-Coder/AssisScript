/* Affine places and lexical loans. Contracts are checked on every concrete
 * function, including indirect calls. Raw legacy references remain separate. */
static Vec memory_scope,memory_places,memory_temps;
static int memory_loop,owned_shape_depth;
static bool resource_type(Type t){return pointer_like(t)||slice_type(t)||equal_type(t,type_str);}
static bool plain_type(Type t){return numeric(t)||floating(t)||equal_type(t,type_bool)||equal_type(t,type_str)||function_value(t)||value_type(t);}
static bool has_owned_fields(Class *c){for(int i=0;i<c->fields.n;i++)if(((Field*)c->fields.v[i])->owned)return true;return false;}
static void owned_type(Type t,Token *where){
    if(slice_type(t))return; /* Borrowed inline descriptor, never an owner. */
    if(value_type(t))error(where,"valor Copy não aceita own; use let ou val");
    if(equal_type(t,type_file))return;
    if(t.depth){if(t.depth!=1||!plain_type(pointed(t))||equal_type(pointed(t),type_str)||function_value(pointed(t)))error(where,"own buffer aceita elementos int, byte ou bool");return;}
    Collection *c=collection_of(t);
    if(c){if(!plain_type(c->key)||(c->map&&!plain_type(c->value)))error(where,"own coleção exige elementos escalares ou text de vida externa");return;}
    Class *cls=object(t)?find_class(t.name):NULL;
    if(!cls)error(where,"own aceita buffers, coleções escalares e structs; classes exigem contrato de destruição");
    if(!cls->record)for(int i=0;i<cls->methods.n;i++){Function *f=cls->methods.v[i];if(!f->receiver_mode)error(where,"classes own exigem contrato de receptor em todos os métodos");}
    if(cls->owned_state)return;if(++owned_shape_depth>256)error(where,"limite de 256 níveis de recursos compostos excedido");cls->owned_state=1;
    for(int i=0;i<cls->fields.n;i++){Field *f=cls->fields.v[i];if(f->owned)owned_type(f->ty,f->t);else if(!plain_type(f->ty))error(where,"own struct exige campos escalares ou campos own explícitos");}
    cls->owned_state=2;owned_shape_depth--;
}
static TypeRef *call_contract(Node *n){return n->fn?function_type(n->fn).ref:n->a->ty.ref;}
static Var *memory_handle(Var *v){while(v&&v->parent)v=v->parent;return v;}
static Var *memory_root(Var *v){v=memory_handle(v);while(v&&v->root)v=memory_handle(v->root);return v;}
static Var *memory_place(Node *n){
    if(!n)return NULL;
    if(n->kind==N_SELF)return checking->receiver;
    if(n->kind==N_NAME)return n->var&&(n->var->ownership||n->var->deferred)?n->var:NULL;
    if(n->kind==N_MEMBER&&n->field&&n->field->owned){
        Var *parent=memory_place(n->a);if(!parent)return NULL;
        if(n->place)return n->place;
        for(int i=0;i<memory_places.n;i++){Var *v=memory_places.v[i];if(v->parent==parent&&v->field_slot==n->slot)return n->place=v;}
        Var *v=mem(sizeof(*v));v->t=n->t;v->ty=n->ty;v->ownership=1;v->parent=parent;v->field_slot=n->slot;v->reg=-1;push(&memory_places,v);return n->place=v;
    }
    return NULL;
}
static Var *managed_origin(Node *n){
    if(!n)return NULL;Var *v=memory_place(n);if(v)return v;
    if(n->kind==N_CALL){TypeRef *r=call_contract(n);return r->result_mode>=2?managed_origin(r->result_from==-1?n->a->a:n->items.v[r->result_from]):NULL;}
    if(n->kind==N_NEW||n->kind==N_ARRAY)return NULL;
    v=managed_origin(n->a);if(v)return v;v=managed_origin(n->b);if(v)return v;
    for(int i=0;i<n->items.n;i++){v=managed_origin(n->items.v[i]);if(v)return v;}return NULL;
}
static void collect_places(Node *n){
    if(!n)return;collect_places(n->a);collect_places(n->b);collect_places(n->c);collect_places(n->step);
    for(int i=0;i<n->items.n;i++)collect_places(n->items.v[i]);(void)memory_place(n);
}
static bool descendant(Var *v,Var *parent){for(;v;v=v->parent)if(v==parent)return true;return false;}
static void memory_alive(Var *v,Token *t,bool whole){
    for(Var *p=v;p;p=p->parent)if(p->moved)error(t,"uso de proprietário movido ou liberado: %s",p->t->text);
    for(Var *p=memory_handle(v);p&&p->root;p=memory_handle(p->root))if(p->root->moved)error(t,"uso de proprietário movido ou liberado");
    if(whole)for(int i=0;i<memory_places.n;i++){Var *p=memory_places.v[i];if(p->moved&&descendant(p,v))error(t,"uso de proprietário parcialmente movido: %s",v->t->text);}
}
static void memory_access(Var *v,Token *t,bool write,bool whole){
    if(!v||v->deferred)return;memory_alive(v,t,whole);Var *h=memory_handle(v);
    if(h->exclusive)error(t,"borrow incompatível: proprietário possui borrow mut ativo: %s",h->t->text);
    if(write&&(h->ownership==2||h->shared))error(t,"mutação exige acesso exclusivo; há borrow ativo");
}
static void loan_add(Var *v,int mode,Token *t,bool temporary){
    if(!v||v->deferred)error(t,"borrow exige o nome de um own ou borrow gerenciado");
    Var *h=memory_handle(v);memory_alive(v,t,true);
    if(h->exclusive||(mode==3&&(h->shared||h->ownership==2)))error(t,"borrow incompatível com empréstimo ativo");
    if(mode==2)h->shared++;else h->exclusive=true;
    if(temporary){push(&memory_temps,h);push(&memory_temps,(void*)(intptr_t)mode);}
}
static void loans_end(int from){
    while(memory_temps.n>from){int mode=(int)(intptr_t)memory_temps.v[--memory_temps.n];Var *v=memory_temps.v[--memory_temps.n];if(mode==2)v->shared--;else v->exclusive=false;}
}
static void reserve_address(Var *v,Token *t){
    Var *h=memory_handle(v);memory_access(h,t,false,false);h->shared++;
    push(&memory_temps,h);push(&memory_temps,(void*)(intptr_t)2);
}
static void no_escape(Node *n){
    Var *v=managed_origin(n);
    if(n&&resource_type(n->ty)&&((v&&!v->deferred)||n->ownership))error(n->t,"referência gerenciada não pode escapar; use contrato borrow ou own");
}
static void memory_expr(Node *n);
/* Intermediate aggregates are not whole reads: an unmoved sibling remains usable. */
static Var *memory_reference(Node *n,bool write,bool whole){
    if(!n)return NULL;
    if(n->kind==N_SELF){Var *v=checking->receiver;memory_access(v,n->t,write,whole);n->ownership=v?v->ownership:0;return v;}
    if(n->kind==N_NAME){Var *v=memory_place(n);memory_access(v,n->t,write,whole);n->ownership=v?memory_handle(v)->ownership:0;return v;}
    if(n->kind==N_MEMBER){
        (void)memory_reference(n->a,false,false);Var *v=managed_origin(n);memory_access(v,n->t,write,whole);n->ownership=n->a->ownership==2?2:v?memory_handle(v)->ownership:0;
        if(write&&n->ownership==2)error(n->t,"mutação exige acesso exclusivo");return v;
    }
    memory_expr(n);Var *v=managed_origin(n);memory_access(v,n->t,write,whole);return v;
}
static void hold_value(Node *n){Var *v=managed_origin(n);if(resource_type(n->ty)&&v&&!v->deferred)loan_add(v,2,n->t,true);}
static Var *borrow_reference(Node *n,int mode){
    Var *v=memory_reference(n,false,true);
    if(mode==3&&n->ownership==2)error(n->t,"borrow mut incompatível com retorno ou referência compartilhada");
    return v;
}
static void memory_consume(Var *v,Token *t,bool whole){
    if(!v||v->ownership!=1||(memory_handle(v)->ownership!=1&&!(v->parent&&memory_handle(v)->ownership==3))||v->root)error(t,"somente own pode ser movido ou liberado");
    memory_alive(v,t,whole);Var *h=memory_handle(v);
    if(h->shared||h->exclusive)error(t,"não é possível mover/liberar proprietário com borrow ativo");
    if(h->loop<memory_loop)error(t,"não é possível consumir proprietário externo dentro de laço");
    v->moved=true;
}
static void memory_take(Node *n){
    if(slice_type(n->ty))error(n->t,"slice não possui os dados; use borrow com origem viva");
    owned_type(n->ty,n->t);
    if(n->kind==N_BUILTIN&&n->op==T_FILE_OPEN){n->ownership=1;memory_expr(n);return;}
    if(n->kind==N_BUILTIN&&n->op==T_MOVE){
        Node *a=n->items.v[0];Var *v=memory_place(a);
        if(!v)error(n->t,"move exige o nome de own ou campo own");
        if(a->kind==N_MEMBER)(void)memory_reference(a->a,false,false);
        memory_consume(v,n->t,true);n->var=v;n->ownership=1;return;
    }
    memory_expr(n);
    if(n->kind!=N_NEW&&n->kind!=N_ARRAY&&!(n->kind==N_BUILTIN&&(n->op==T_BUFFER||n->op==T_ALLOC))&&!(n->kind==N_CALL&&call_contract(n)->result_mode==1))error(n->t,"own exige alocação nova, retorno own ou move(proprietario)");
    n->ownership=1;
}
static void memory_arguments(Node *n,TypeRef *r){
    for(int i=0;i<n->items.n;i++){
        Node *a=n->items.v[i];int mode=parameter_mode(r,i);
        if(mode==1)memory_take(a);
        else if(mode>=2){Var *v=borrow_reference(a,mode);loan_add(v,mode,a->t,true);}
        else{memory_expr(a);no_escape(a);}
    }
}
static void memory_expr(Node *n){
    if(n&&n->kind==N_BUILTIN&&n->op==T_SLICE_MAKE){
        int old=memory_temps.n;Node *input=n->items.v[0];Var *v=memory_reference(input,false,true);
        if(!v||!input->ownership)error(n->t,"fatia exige buffer ou slice gerenciado");
        loan_add(v,2,n->t,true);memory_expr(n->items.v[1]);memory_expr(n->items.v[2]);loans_end(old);n->ownership=input->ownership;return;
    }
    if(!n)return;
    if(n->kind==N_BUILTIN&&n->op==T_FILE_OPEN){if(n->ownership!=1)error(n->t,"arquivo_abrir exige destino own ou retorno own");memory_expr(n->items.v[0]);hold_value(n->items.v[0]);memory_expr(n->items.v[1]);return;}
    if(n->kind==N_BUILTIN&&(n->op==T_FILE_READ||n->op==T_FILE_WRITE||n->op==T_FILE_CLOSE||n->op==T_FILE_SYNC||n->op==T_ARG_COPY||n->op==T_WRITE_BYTES)){
        int old=memory_temps.n,buffer=(n->op==T_FILE_CLOSE||n->op==T_FILE_SYNC)?-1:1;
        if(n->op==T_ARG_COPY||n->op==T_WRITE_BYTES)memory_expr(n->items.v[0]);
        else{Node *file=n->items.v[0];Var *v=borrow_reference(file,3);loan_add(v,3,n->t,true);}
        if(buffer>=0){Node *b=n->items.v[buffer];Var *v=memory_reference(b,false,true);if(v&&!v->deferred){int mode=(n->op==T_FILE_WRITE||n->op==T_WRITE_BYTES)?2:3;if(mode==3&&b->ownership==2)error(n->t,"IO exige buffer mutável");loan_add(v,mode,n->t,true);}memory_expr(n->items.v[2]);}
        loans_end(old);return;
    }
    if(n->kind==N_NAME||n->kind==N_MEMBER||n->kind==N_SELF){(void)memory_reference(n,false,resource_type(n->ty));return;}
    if(n->kind==N_BUILTIN&&n->op==T_MOVE)error(n->t,"move só pode inicializar own, argumento own ou retorno own");
    Var *origin=managed_origin(n);
    if(origin&&!origin->deferred&&((n->kind==N_UNARY&&(n->op=='&'||n->op=='*'))||(n->kind==N_BINARY&&n->ty.depth)||(n->kind==N_BUILTIN&&(n->op==T_TEXT||n->op==T_BYTES))))error(n->t,"ponteiro gerenciado exige indexação verificada; extração de ponteiro bruto não é permitida");
    if(n->kind==N_CALL){
        int old=memory_temps.n;
        if(!n->fn)memory_expr(n->a);
        if(n->fn&&n->fn->owner){
            Var *v=memory_reference(n->a->a,false,true);
            if(v&&!v->deferred){
                Collection *c=collection_of(n->a->a->ty);const char *name=n->a->t->text;
                if((!c&&!n->fn->receiver_mode)||(c&&(name[0]=='_'||same(name,"dispose"))))error(n->t,"método não permitido em referência gerenciada");
                bool read=c?(same(name,"get")||same(name,"get_or")||same(name,"contains")||same(name,"has")):n->fn->receiver_mode==2;
                if(!read){if(n->a->a->ownership==2)error(n->t,"mutação exige acesso exclusivo");memory_access(v,n->t,true,true);}loan_add(v,read?2:3,n->t,true);
            }
        }
        TypeRef *r=call_contract(n);memory_arguments(n,r);loans_end(old);n->ownership=r->result_mode;return;
    }
    if(n->kind==N_NEW){
        int old=memory_temps.n;
        if(n->cls->value){for(int i=0;i<n->items.n;i++)memory_expr(n->items.v[i]);}
        else if(n->cls->record){
            for(int i=0;i<n->items.n;i++){Node *a=n->items.v[i];Field *f=n->cls->fields.v[i];if(f->owned)memory_take(a);else{memory_expr(a);no_escape(a);}}
            if(has_owned_fields(n->cls))n->ownership=1;
        }else if(n->fn)memory_arguments(n,function_type(n->fn).ref);
        loans_end(old);return;
    }
    if(n->kind==N_INDEX){
        int old=memory_temps.n;Var *v=memory_reference(n->a,false,true);hold_value(n->a);memory_expr(n->b);loans_end(old);
        if(v&&!n->a->ownership)n->a->ownership=memory_handle(v)->ownership;n->ownership=n->a->ownership;return;
    }
    if(n->kind==N_BINARY){memory_expr(n->a);hold_value(n->a);memory_expr(n->b);return;}
    if(n->kind==N_BUILTIN&&n->op==T_READ){
        int old=memory_temps.n;Node *a=n->items.v[0];Var *v=memory_reference(a,false,true);
        if(v&&!v->deferred){if(a->ownership==2)error(n->t,"ler_bytes exige acesso exclusivo");memory_access(v,n->t,true,true);loan_add(v,3,n->t,true);}
        memory_expr(n->items.v[1]);loans_end(old);return;
    }
    memory_expr(n->a);memory_expr(n->b);
    for(int i=0;i<n->items.n;i++){Node *a=n->items.v[i];memory_expr(a);if(n->kind==N_ARRAY)no_escape(a);else hold_value(a);}
    if(n->kind==N_BUILTIN&&n->op==T_LEN&&((Node*)n->items.v[0])->ty.depth&&!((Node*)n->items.v[0])->ownership)error(n->t,"len de buffer exige own/borrow gerenciado");
}
static bool *memory_snapshot(void){bool *s=mem((size_t)memory_places.n);for(int i=0;i<memory_places.n;i++)s[i]=((Var*)memory_places.v[i])->moved;return s;}
static void memory_restore(bool *s){for(int i=0;i<memory_places.n;i++)((Var*)memory_places.v[i])->moved=s[i];}
static int memory_stmt(Node *n){
    int flow=FLOW_NORMAL;
    switch(n->kind){
    case N_UNSAFE:flow=memory_stmt(n->a);break;
    case N_BLOCK:{
        int old=memory_scope.n;
        for(int i=0;i<n->items.n;i++){
            bool *dead=(flow&FLOW_NORMAL)?NULL:memory_snapshot();int f=memory_stmt(n->items.v[i]);
            if(dead){memory_restore(dead);free(dead);}else flow=(flow&~FLOW_NORMAL)|f;
        }
        for(int i=memory_scope.n-1;i>=old;i--){Var *v=memory_scope.v[i];if(v->root){if(v->ownership==2)v->root->shared--;if(v->ownership==3)v->root->exclusive=false;}}
        memory_scope.n=old;break;
    }
    case N_LET:{
        Var *v=n->var;v->loop=memory_loop;v->moved=false;
        if(slice_type(v->ty)&&v->ownership<2)error(n->t,"slice exige vínculo borrow");
        if(v->ownership==1)memory_take(n->a);
        else if(v->ownership>=2){
            Var *source=borrow_reference(n->a,v->ownership);loans_end(0);
            if(!source||!resource_type(v->ty))error(n->t,"borrow exige o nome de um own ou borrow gerenciado");
            loan_add(source,v->ownership,n->t,false);v->root=memory_handle(source);
        }else{memory_expr(n->a);no_escape(n->a);}
        push(&memory_scope,v);break;
    }
    case N_ASSIGN:{
        Var *v=managed_origin(n->a);bool owned_field=n->a->kind==N_MEMBER&&n->a->field->owned;
        if(owned_field){
            if(!v||!memory_place(n->a))error(n->t,"campo own exige posição em proprietário gerenciado");
            (void)memory_reference(n->a->a,false,false);memory_access(memory_handle(v),n->t,true,false);
            if(n->op!='=')error(n->t,"campo own aceita somente atribuição simples");
        }else{
            memory_expr(n->a);
            if(n->a->ownership==2)error(n->t,"mutação exige acesso exclusivo");
            if(v&&n->a->kind==N_NAME)error(n->t,"referência own/borrow/defer não pode ser reatribuída");
            memory_access(v,n->t,true,false);
        }
        /* Reserve the saved address: reads are permitted while the RHS runs. */
        int old=memory_temps.n;if(v&&!v->deferred)reserve_address(v,n->t);
        if(owned_field){memory_take(n->b);n->replace_owned=true;v->moved=false;for(int i=0;i<memory_places.n;i++){Var *p=memory_places.v[i];if(descendant(p,v))p->moved=false;}}
        else{memory_expr(n->b);no_escape(n->b);}loans_end(old);break;
    }
    case N_FREE:case N_DEFER:{
        Var *v=managed_origin(n->a);
        if(n->kind==N_DEFER){memory_expr(n->a);if(n->a->kind!=N_NAME||v)error(n->t,"defer free exige variável let ainda não gerenciada");n->a->var->deferred=true;n->var=n->a->var;}
        else if(v){if(v->deferred||!memory_place(n->a))error(n->t,"free exige proprietário original sem defer");memory_consume(v,n->t,false);n->var=v;}
        else memory_expr(n->a);break;
    }
    case N_IF:{
        memory_expr(n->a);loans_end(0);bool *before=memory_snapshot();int yes=memory_stmt(n->b);bool *after=memory_snapshot();memory_restore(before);
        int no=n->c?memory_stmt(n->c):FLOW_NORMAL;
        for(int i=0;i<memory_places.n;i++){Var *v=memory_places.v[i];if(!(no&FLOW_NORMAL))v->moved=(yes&FLOW_NORMAL)?after[i]:before[i];else if(yes&FLOW_NORMAL)v->moved|=after[i];}
        free(before);free(after);flow=yes|no;break;
    }
    case N_MATCH:{
        memory_expr(n->a);loans_end(0);bool *before=memory_snapshot(),*joined=mem((size_t)memory_places.n);flow=0;bool live=false;
        for(int i=0;i<n->items.n;i++){
            memory_restore(before);Node *arm=n->items.v[i];int f=memory_stmt(arm->a);flow|=f;
            if(f&FLOW_NORMAL){live=true;for(int j=0;j<memory_places.n;j++)joined[j]|=((Var*)memory_places.v[j])->moved;}
        }
        memory_restore(live?joined:before);free(before);free(joined);break;
    }
    case N_WHILE:{
        memory_loop++;memory_expr(n->a);loans_end(0);int body=memory_stmt(n->b);if(n->step)memory_stmt(n->step);memory_loop--;
        flow=(body&FLOW_RETURN)|FLOW_NORMAL;break;
    }
    case N_RETURN:
        if(n->a&&checking->result_mode==1)memory_take(n->a);
        else if(n->a&&checking->result_mode>=2){
            Var *v=borrow_reference(n->a,checking->result_mode);loans_end(0);Var *expected=checking->result_from==-1?checking->receiver:checking->params.v[checking->result_from];
            if(!v||memory_root(v)!=expected)error(n->t,"retorno borrow deve derivar do parâmetro declarado; referência local não pode escapar");
            loan_add(v,checking->result_mode,n->t,true);
        }else{memory_expr(n->a);no_escape(n->a);}flow=FLOW_RETURN;break;
    case N_PRINT:for(int i=0;i<n->items.n;i++){Node *a=n->items.v[i];memory_expr(a);hold_value(a);}break;
    case N_EXPR:memory_expr(n->a);no_escape(n->a);break;
    case N_BREAK:flow=FLOW_BREAK;break;
    case N_CONTINUE:flow=FLOW_CONTINUE;break;
    default:break;
    }
    loans_end(0);return flow;
}
static void check_ownership(void){
    for(int i=0;i<classes.n;i++){Class *c=classes.v[i];instantiation_site=c->site;instantiation_name=c->generic?c->generic->t->text:NULL;for(int j=0;j<c->fields.n;j++){Field *f=c->fields.v[j];if(f->owned)owned_type(f->ty,f->t);}}instantiation_site=NULL;
    for(int i=0;i<all_functions.n;i++){
        checking=all_functions.v[i];memory_scope.n=0;memory_places.n=0;memory_temps.n=0;memory_loop=0;
        instantiation_site=checking->site;instantiation_name=checking->generic?checking->generic->t->text:NULL;
        for(int j=0;j<checking->vars.n;j++)push(&memory_places,checking->vars.v[j]);collect_places(checking->body);
        if(checking->receiver)push(&memory_places,checking->receiver);
        if(checking->result_mode==1)owned_type(checking->result,checking->t);
        for(int j=0;j<checking->params.n;j++){Var *p=checking->params.v[j];if(p->ownership&&(!equal_type(p->ty,type_str)||p->ownership==1))owned_type(p->ty,p->t);}
        memory_stmt(checking->body);
    }
    instantiation_site=NULL;
}
