function CollapseBtn({ menuCollapse, setMenuCollapse }) {

    const CollapseMenu = ()=>{
        setMenuCollapse(menuCollapse?0:1);
    }

    window.addEventListener('resize', (e)=>{
        const m = e.target.innerWidth<820;
        setMenuCollapse(m?0:1);
    });

    return (
        <div className='collapse-btn'>
            <button onClick={CollapseMenu}>
                {menuCollapse?
                    <>&times;</>
                :
                    <>&equiv;</>
                }
            </button>
        </div>
    );
}

export default CollapseBtn;