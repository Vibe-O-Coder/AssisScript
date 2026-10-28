/* Global scalar register allocation over the typed CFG. Calls preserve the
 * four selected callee-saved registers. Addressed locals always stay in memory.
 * Bounded analyses fall back to the original frequency allocator. */
#define REG_LIMIT 256
#define REG_WORDS (REG_LIMIT/64)
typedef struct {uint64_t words[REG_WORDS];} RegSet;
typedef struct {RegSet use,def,in,out;} RegLive;
static void reg_add(RegSet *s,int i){if(i>=0)s->words[i/64]|=UINT64_C(1)<<(i%64);}
static bool reg_has(RegSet s,int i){return (s.words[i/64]>>(i%64))&1;}
static RegSet reg_union(RegSet a,RegSet b){for(int w=0;w<REG_WORDS;w++)a.words[w]|=b.words[w];return a;}
static RegSet reg_transfer(RegSet live,RegSet use,RegSet def){for(int w=0;w<REG_WORDS;w++)live.words[w]=(live.words[w]&~def.words[w])|use.words[w];return live;}
static bool reg_equal(RegSet a,RegSet b){return !memcmp(&a,&b,sizeof(a));}
static int reg_index(Vec *vars,Var *v){for(int i=0;i<vars->n;i++)if(vars->v[i]==v)return i;return -1;}
static void count_uses(Node *n,int depth){
    if(!n||n->unreachable)return;int weight=1<<(depth>4?12:depth*3);
    if(n->kind==N_NAME&&n->var){int *uses=&n->var->uses;*uses=*uses>INT_MAX-weight?INT_MAX:*uses+weight;}
    int nested=n->kind==N_WHILE?depth+1:depth;
    count_uses(n->a,nested);count_uses(n->b,nested);count_uses(n->c,depth);count_uses(n->step,nested);
    for(int i=0;i<n->items.n;i++)count_uses(n->items.v[i],depth);
}
static void reg_names(Node *n,Vec *vars,RegSet *use){
    if(!n)return;if(n->kind==N_NAME)reg_add(use,reg_index(vars,n->var));
    reg_names(n->a,vars,use);reg_names(n->b,vars,use);reg_names(n->c,vars,use);reg_names(n->step,vars,use);
    for(int i=0;i<n->items.n;i++)reg_names(n->items.v[i],vars,use);
}
static void reg_operation(Node *n,Vec *vars,RegSet *use,RegSet *def){
    if(n->kind==N_UNSAFE)return; /* Marker; child statements have their own ops. */
    if(n->kind==N_LET||n->kind==N_NAME){reg_add(def,reg_index(vars,n->var));reg_names(n->a,vars,use);return;}
    if(n->kind==N_ASSIGN&&n->a->kind==N_NAME){reg_add(def,reg_index(vars,n->a->var));if(n->op!='=')reg_names(n->a,vars,use);reg_names(n->b,vars,use);return;}
    reg_names(n,vars,use);
}
static void reg_clique(RegSet *edges,RegSet live,int count){
    for(int i=0;i<count;i++)if(reg_has(live,i)){edges[i]=reg_union(edges[i],live);edges[i].words[i/64]&=~(UINT64_C(1)<<(i%64));}
}
static void reg_fallback(IRFunction *f,Vec vars){
    const int registers[]={3,12,13,14};
    for(int r=0;r<4;r++){Var *best=NULL;for(int i=0;i<vars.n;i++){Var *v=vars.v[i];if(v->reg<0&&(!best||v->uses>best->uses))best=v;}if(best){best->reg=registers[r];f->register_variables++;}}free(vars.v);
}
static void allocate_registers(IRFunction *f){
    if(!optimize||f->source->foreign)return;count_uses(f->source->body,0);Vec vars={0};
    for(int i=0;i<f->source->vars.n;i++){Var *v=f->source->vars.v[i];if(!v->address_taken&&ir_scalar(v->ty)&&v->uses)push(&vars,v);}
    if(!vars.n)return;
    /* DWARF currently describes one location per lexical variable, without
     * location lists. Keep those registers unique even after their last use. */
    if(debug_symbols||vars.n>REG_LIMIT||f->blocks.n>4096){reg_fallback(f,vars);return;}
    RegLive *blocks=mem((size_t)f->blocks.n*sizeof(*blocks));RegSet *edges=mem((size_t)vars.n*sizeof(*edges));
    for(int i=0;i<f->blocks.n;i++){
        IRBlock *b=f->blocks.v[i];RegLive *l=&blocks[i];
        for(int j=0;j<b->operations.n;j++){RegSet use={0},def={0};reg_operation(((IROperation*)b->operations.v[j])->node,&vars,&use,&def);for(int w=0;w<REG_WORDS;w++)l->use.words[w]|=use.words[w]&~l->def.words[w];l->def=reg_union(l->def,def);}
        RegSet condition={0};reg_names(b->condition,&vars,&condition);for(int w=0;w<REG_WORDS;w++)l->use.words[w]|=condition.words[w]&~l->def.words[w];
    }
    bool changed=true;int iterations=0;
    while(changed&&++iterations<=8192){
        changed=false;
        for(int i=f->blocks.n-1;i>=0;i--){IRBlock *b=f->blocks.v[i];RegLive *l=&blocks[i];RegSet out={0};for(int j=0;j<b->successors.n;j++)out=reg_union(out,blocks[(int)(intptr_t)b->successors.v[j]-1].in);RegSet in=reg_transfer(out,l->use,l->def);if(!reg_equal(in,l->in)||!reg_equal(out,l->out)){l->in=in;l->out=out;changed=true;}}
    }
    if(changed){free(blocks);free(edges);reg_fallback(f,vars);return;}
    for(int i=0;i<f->blocks.n;i++){
        IRBlock *b=f->blocks.v[i];RegSet live=blocks[i].out,condition={0};reg_names(b->condition,&vars,&condition);live=reg_union(live,condition);reg_clique(edges,live,vars.n);
        for(int j=b->operations.n-1;j>=0;j--){RegSet use={0},def={0};reg_operation(((IROperation*)b->operations.v[j])->node,&vars,&use,&def);
            /* Even a dead definition writes its assigned physical register. */
            for(int d=0;d<vars.n;d++)if(reg_has(def,d))for(int v=0;v<vars.n;v++)if(d!=v&&reg_has(live,v)){reg_add(&edges[d],v);reg_add(&edges[v],d);}
            live=reg_transfer(live,use,def);reg_clique(edges,live,vars.n);
        }
    }
    /* All parameters are assigned at entry, including those dead on a path.
     * This also makes simultaneous tail-call parameter replacement safe. */
    RegSet parameters=blocks[0].in;for(int i=0;i<f->source->params.n;i++)reg_add(&parameters,reg_index(&vars,f->source->params.v[i]));reg_clique(edges,parameters,vars.n);
    const int registers[]={3,12,13,14};bool *done=mem((size_t)vars.n);unsigned used=0;
    for(int pass=0;pass<vars.n;pass++){
        int best=-1;for(int i=0;i<vars.n;i++)if(!done[i]&&(best<0||((Var*)vars.v[i])->uses>((Var*)vars.v[best])->uses))best=i;done[best]=true;Var *v=vars.v[best];
        for(int r=0;r<4;r++){bool conflict=false;for(int j=0;j<vars.n;j++)if(reg_has(edges[best],j)&&((Var*)vars.v[j])->reg==registers[r]){conflict=true;break;}if(!conflict){v->reg=registers[r];f->register_variables++;used|=1u<<r;break;}}
    }
    for(int r=0;r<4;r++)if(used&(1u<<r))f->register_reuses--;
    f->register_reuses+=f->register_variables;f->liveness=true;free(done);free(blocks);free(edges);free(vars.v);
}
static void prepare_registers(void){for(int i=0;i<ir_functions.n;i++)allocate_registers(ir_functions.v[i]);}
